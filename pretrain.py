import torch
import torch.nn as nn
import os
import pandas as pd
import numpy as np
from torch.utils.data import Dataset, DataLoader, TensorDataset
from transformers import AutoTokenizer, AutoModel
from models.actor import ActorHead

def build_embeddings(telemetry_path, model_id, device):
    """Run Granite once on all telemetry rows and save embeddings to disk."""
    
    cache_path = 'checkpoints/embeddings_cache.pt'
    
    # If cache exists load it
    if os.path.exists(cache_path):
        print("Loading cached embedds")
        cache = torch.load(cache_path)
        #loads embeds actions and size for torch
        return cache['embeddings'], cache['actions'], cache['hidden_dim']
    
    print("Building embedds vv")
    
    state_cols = ['speedX', 'speedY', 'speedZ', 'rpm'] + \
             [f'track_{i}' for i in range(19)] + \
             [f'wheelSpinVel_{i}' for i in range(4)]
             
    action_cols = ['steer', 'accel', 'brake']
    
    # Loads dataset from hardcoded bot
    df = pd.read_csv(telemetry_path[0])
    print(f"Total rows: {len(df)}")
    
    # Filter bad states
    before = len(df)
    df = df[df['speedX'] > 5 ]
    df = df[df['track_0'] > 0 ]
    df = df[df['track_9'] > 0 ]
    df = df[df['track_18'] > 0 ]
    
    df = df.reset_index(drop=True)
    print(f"Rows before: {before} - Rows post filter {len(df)}")
    
    
    # Tokenise inputs for grantie to give ID's
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    granite = AutoModel.from_pretrained(model_id, dtype=torch.float16).to(device)
    granite.eval()
    hidden_dim = granite.config.hidden_size
    
    all_embeddings = []
    all_actions = []
    
    # reduces batch size to fgit into memory
    batch_size = 1
    total = len(df)
    
    #feed granite tokenized dataframe to generate embeddings of the data
    with torch.no_grad():
        for i in range(total):
            row = df.iloc[i]
            
            #adds semantic to data so granite can evaluate 
            parts = []
            for col in state_cols:
                value = row[col]
                parts.append(f"{col}: {value:.3f}")
            text = ", ".join(parts)
            
            #tokenize text - converts to PyTorch tensor inputs
            inputs = tokenizer(text, return_tensors = "pt", truncation = True, max_length = 512)
            inputs = {key: val.to(device) for key, val in inputs.items()}
            
            #runs granite with evaluated tokens to get state outputs
            output = granite(**inputs)
            
            #loads whole input sequence as vector
            embedding = output.last_hidden_state[:, 0, :] 
            #normalise vectors
            embedding = torch.nn.functional.normalize(embedding, dim=1)
            
            all_embeddings.append(embedding.float().cpu())
            
            #convers current rows actions into a tensor
            steer = float(row['steer'])
            accel = float(row['accel'])
            brake = float(row['brake'])
            action = torch.tensor([[steer, accel, brake]], dtype=torch.float32)
            all_actions.append(action)
            
            if i % 500 == 0:
                print(f"  Processed {i}/{total} rows")

            torch.cuda.empty_cache()
        
        
    # combines embeddings and actions tensors into their respective tensor 
    all_embeddings = torch.cat(all_embeddings, dim = 0)
    all_actions = torch.cat(all_actions, dim = 0)
    
    # saves embeddings
    os.makedirs('checkpoints', exist_ok=True)
    torch.save({
        'embeddings': all_embeddings,
        'actions': all_actions,
        'hidden_dim': hidden_dim
    }, cache_path)
    print(f"Embeddings saved to {cache_path}")
    
    # frees memory
    del granite
    torch.cuda.empty_cache()
    
    return all_embeddings, all_actions, hidden_dim



def pretrain_actor(telemetry_path, epochs=500, lr=5e-5):
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Pretraining on: {device}")
    
    #model_id = "ibm-granite/granite-embedding-125m-english"
    model_id = "ibm-granite/granite-embedding-english-r2"
    
    # build embeddings
    embeddings, actions, hidden_dim = build_embeddings(telemetry_path, model_id, device)
    
    print(f"Embeddings shape: {embeddings.shape}")
    print(f"Actions shape: {actions.shape}")
    
    # train actor on embeddings
    dataset = TensorDataset(embeddings, actions)
    loader = DataLoader(dataset, batch_size=64, shuffle=True)
    
    #loads actor network to train into
    actor = ActorHead(input_dim=hidden_dim, action_dim=3).to(device)
    
    resume_path = 'checkpoints/pretrained_actor.pt'
    if os.path.exists(resume_path):
        actor.load_state_dict(torch.load(resume_path, map_location='cpu'))
        print("resuming with existing model")
    
    #uses adam optimisation for uncertaint and decision gradients
    optimiser = torch.optim.Adam(actor.parameters(), lr=lr)
    
    best_loss = float('inf')
    os.makedirs('checkpoints', exist_ok=True)
    
    print(f"\nTraining actor for {epochs} epochs...")
    
    for epoch in range(epochs):
        total_loss = 0
        
        for embedding_batch, action_batch in loader:
            embedding_batch = embedding_batch.to(device)
            action_batch = action_batch.to(device)
            
            predicted = actor(embedding_batch)
            
            #matches inputs against predicted and calculates mse per input
            loss = nn.functional.mse_loss(predicted, action_batch)
            
            optimiser.zero_grad()
            loss.backward()
            optimiser.step()
            total_loss += loss.item()
           
        avg_loss = total_loss / len(loader)
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs} - Loss:{avg_loss:.6f}")
            
        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(actor.state_dict(), 'checkpoints/pretrained_actor.pt')
    
    print(f"\nPretraining complete. Best loss: {best_loss:.6f}")
    print("Weights saved to checkpoints/pretrained_actor.pt")


if __name__ == "__main__":
    path = [
        '/home/myles/Work/Torcs-Proj/Torcs-Package/gym_torcs/telemetry/bot_20260316_220349.csv'
    ]
    pretrain_actor(path, epochs = 250, lr=1e-5)