import os
import io
import base64
import pandas as pd
import numpy as np
from fastapi import FastAPI, BackgroundTasks
from apscheduler.schedulers.background import BackgroundScheduler
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt

app = FastAPI(title="VibeCheck Bonding Engine")
scheduler = BackgroundScheduler()

# Mock Database connection
def get_all_active_users():
    # In reality, this pulls from PostgreSQL
    # Columns: user_id, spotify_valence, spotify_danceability, twitter_neuroticism, humor_darkness
    return pd.DataFrame({
        'user_id': ['u1', 'u2', 'u3', 'u4', 'u5'],
        'spotify_valence': [0.8, 0.7, 0.2, 0.9, 0.3],
        'spotify_danceability': [0.6, 0.5, 0.1, 0.8, 0.2],
        'twitter_neuroticism': [0.4, 0.5, 0.9, 0.3, 0.8],
        'humor_darkness': [0.5, 0.6, 0.9, 0.2, 0.8]
    })

def generate_match_graph(user_data, match_data, score):
    """Generates a radar chart comparing the vibes, returns base64 image for the UI"""
    labels = np.array(['Valence', 'Danceability', 'Neuroticism', 'Dark Humor'])
    user_stats = user_data[['spotify_valence', 'spotify_danceability', 'twitter_neuroticism', 'humor_darkness']].values[0]
    match_stats = match_data[['spotify_valence', 'spotify_danceability', 'twitter_neuroticism', 'humor_darkness']].values[0]
    
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False)
    user_stats = np.concatenate((user_stats,[user_stats[0]]))
    match_stats = np.concatenate((match_stats,[match_stats[0]]))
    angles = np.concatenate((angles,[angles[0]]))
    
    fig = plt.figure(figsize=(4,4))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, user_stats, 'o-', linewidth=2, label='You', color='#9333EA')
    ax.fill(angles, user_stats, alpha=0.25, color='#9333EA')
    ax.plot(angles, match_stats, 'o-', linewidth=2, label='Match', color='#10B981')
    ax.fill(angles, match_stats, alpha=0.25, color='#10B981')
    ax.set_thetagrids(angles[:-1] * 180/np.pi, labels)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return image_base64

def calculate_nightly_matches():
    """Cronjob: Calculates top 3 matches to incentivize real bonding"""
    print("Initiating nightly bonding vector calculation...")
    df = get_all_active_users()
    features = ['spotify_valence', 'spotify_danceability', 'twitter_neuroticism', 'humor_darkness']
    
    vector_matrix = df[features].values
    similarity_matrix = cosine_similarity(vector_matrix)
    
    matches_db = {}
    
    # Loop through each user to find their top 3
    for idx, user_row in df.iterrows():
        user_id = user_row['user_id']
        # Get similarities, ignoring self (which is 1.0 at similarity_matrix[idx][idx])
        sim_scores = list(enumerate(similarity_matrix[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        top_3 = []
        for i, score in sim_scores:
            if i != idx and len(top_3) < 3:
                match_id = df.iloc[i]['user_id']
                
                # Generate the visual proof of bonding compatibility
                graph_b64 = generate_match_graph(
                    df[df['user_id'] == user_id], 
                    df[df['user_id'] == match_id], 
                    score
                )
                
                top_3.append({
                    "match_id": match_id,
                    "compatibility_score": round(score * 100, 2),
                    "graph_overlay": graph_b64
                })
                
        matches_db[user_id] = top_3
        print(f"Locked top 3 for {user_id}. Ready for deployment.")
        
    # In reality, bulk insert matches_db into the database here
    # Overwriting the previous day's matches to force action before they disappear

@app.on_event("startup")
def start_scheduler():
    # Run at 3:00 AM every night
    scheduler.add_job(calculate_nightly_matches, 'cron', hour=3, minute=0)
    scheduler.start()

@app.on_event("shutdown")
def stop_scheduler():
    scheduler.shutdown()