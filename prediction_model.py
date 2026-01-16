import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class EnrollmentPredictionModel(nn.Module):
    def __init__(self, input_size=1, hidden_size=50, num_layers=2):
        super(EnrollmentPredictionModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)

        self.fc = nn.Linear(hidden_size, 1)
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, x):

        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)

        out, _ = self.lstm(x, (h0, c0))

        out = self.dropout(out[:, -1, :])
        out = self.fc(out)
        return out

def prepare_time_series_data(df, target_col='age_0_5'):
    """
    Prepare time series data for training the model
    """

    df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
    df = df.sort_values('date')

    monthly_data = df.groupby(df['date'].dt.to_period('M'))[target_col].sum().reset_index()
    monthly_data['date'] = monthly_data['date'].dt.to_timestamp()

    monthly_data['month_num'] = monthly_data['date'].dt.month
    monthly_data['year'] = monthly_data['date'].dt.year

    target_values = monthly_data[target_col].values.astype(float)
    min_val, max_val = target_values.min(), target_values.max()
    if max_val != min_val:
        normalized_targets = (target_values - min_val) / (max_val - min_val)
    else:
        normalized_targets = target_values
    
    return monthly_data, normalized_targets, min_val, max_val

def train_prediction_model(df, target_col='age_0_5', epochs=100):
    """
    Train the PyTorch model for enrollment prediction
    """

    monthly_data, normalized_targets, min_val, max_val = prepare_time_series_data(df, target_col)
    
    if len(normalized_targets) < 10:  
        raise ValueError("Insufficient data for training. Need at least 10 data points.")

    sequence_length = min(6, len(normalized_targets) - 1)  
    X, y = [], []
    
    for i in range(len(normalized_targets) - sequence_length):
        X.append(normalized_targets[i:i+sequence_length])
        y.append(normalized_targets[i+sequence_length])
    
    if len(X) == 0:
        raise ValueError("Not enough data to create sequences for training.")
    
    X = np.array(X)
    y = np.array(y)

    X_tensor = torch.FloatTensor(X).unsqueeze(-1)  
    y_tensor = torch.FloatTensor(y).unsqueeze(-1)

    model = EnrollmentPredictionModel(input_size=1, hidden_size=50, num_layers=2)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        outputs = model(X_tensor)
        loss = criterion(outputs, y_tensor)
        loss.backward()
        optimizer.step()
        
        if (epoch + 1) % 50 == 0:
            print(f'Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}')
    
    return model, sequence_length, min_val, max_val, monthly_data

def predict_next_month(model, last_sequence, min_val, max_val):
    """
    Predict the next month's enrollment using the trained model
    """
    model.eval()
    with torch.no_grad():

        seq_tensor = torch.FloatTensor(last_sequence).unsqueeze(0).unsqueeze(-1)
        prediction = model(seq_tensor)
        pred_normalized = prediction.item()

        if max_val != min_val:
            prediction_denorm = pred_normalized * (max_val - min_val) + min_val
        else:
            prediction_denorm = pred_normalized
            
        return max(0, prediction_denorm)  

def calculate_growth_rate(current_val, previous_val):
    """
    Calculate the growth rate between two values
    """
    if previous_val == 0:
        return float('inf') if current_val > 0 else 0
    return ((current_val - previous_val) / previous_val) * 100

def analyze_trends(monthly_data):
    """
    Analyze trends in the data to provide insights
    """
    if len(monthly_data) < 2:
        return "Insufficient data for trend analysis"

    monthly_data = monthly_data.sort_values('date')
    monthly_data['prev_month'] = monthly_data['age_0_5'].shift(1)
    monthly_data['growth_rate'] = ((monthly_data['age_0_5'] - monthly_data['prev_month']) / 
                                   monthly_data['prev_month'] * 100).fillna(0)
    
    avg_growth = monthly_data['growth_rate'].mean()
    recent_trend = monthly_data['growth_rate'].tail(3).mean()  

    monthly_avg = monthly_data.groupby('month_num')['age_0_5'].mean()
    peak_month = monthly_avg.idxmax() if len(monthly_avg) > 0 else None
    lowest_month = monthly_avg.idxmin() if len(monthly_avg) > 0 else None
    
    insights = {
        'average_growth_rate': avg_growth,
        'recent_trend': recent_trend,
        'peak_month': peak_month,
        'lowest_month': lowest_month,
        'total_months': len(monthly_data),
        'latest_value': monthly_data['age_0_5'].iloc[-1] if len(monthly_data) > 0 else 0
    }
    
    return insights