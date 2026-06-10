"""
train_models.py
Run this once to train and save the ML models using scikit-learn.
Models saved to: ml_models/
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score
from sklearn.preprocessing import LabelEncoder

SAVE_DIR = os.path.join(os.path.dirname(__file__))
os.makedirs(SAVE_DIR, exist_ok=True)

# ─── 1. FARE PREDICTION — Linear Regression ─────────────────

print("Training Fare Regression Model...")
np.random.seed(42)
N = 1000

distances = np.random.randint(1, 20, N)
hours = np.random.randint(0, 24, N)
pax = np.random.randint(1, 6, N)
peak = ((hours >= 7) & (hours <= 10)) | ((hours >= 17) & (hours <= 20))
peak_mult = np.where(peak, 1.25, np.where((hours >= 11) & (hours <= 14), 1.0, 0.9))
discount = np.where(pax >= 4, 0.88, np.where(pax >= 3, 0.92, np.where(pax >= 2, 0.96, 1.0)))
fare_per_stop = 1.2 * 0.8
fares = (5.0 + fare_per_stop * distances) * peak_mult * discount * pax + np.random.normal(0, 0.5, N)

X_fare = np.column_stack([distances, hours, pax, peak.astype(int)])
y_fare = fares

X_train, X_test, y_train, y_test = train_test_split(X_fare, y_fare, test_size=0.2)
lr = LinearRegression()
lr.fit(X_train, y_train)
y_pred = lr.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
print(f"  Fare RMSE: ₹{rmse:.2f}")
print(f"  R² Score : {lr.score(X_test, y_test):.4f}")

with open(os.path.join(SAVE_DIR, 'fare_model.pkl'), 'wb') as f:
    pickle.dump(lr, f)
print("  ✅ Saved: fare_model.pkl")

# ─── 2. CROWD PREDICTION — Regression ───────────────────────

print("\nTraining Crowd Regression Model...")
PATTERN = {0:8,1:5,2:4,3:3,4:5,5:12,6:35,7:72,8:91,9:88,10:65,11:55,
           12:60,13:58,14:50,15:52,16:68,17:85,18:95,19:90,20:75,21:55,22:35,23:18}

hours_c  = np.random.randint(0, 24, N)
route_ids = np.random.randint(1, 7, N)
base_crowd = np.array([PATTERN[h] for h in hours_c])
crowd = np.clip(base_crowd * (1 + (route_ids - 3) * 0.05) + np.random.normal(0, 5, N), 0, 100).astype(int)

X_crowd = np.column_stack([hours_c, route_ids])
y_crowd = crowd

Xc_train, Xc_test, yc_train, yc_test = train_test_split(X_crowd, y_crowd, test_size=0.2)
lr_crowd = LinearRegression()
lr_crowd.fit(Xc_train, yc_train)
rmse_c = np.sqrt(mean_squared_error(yc_test, lr_crowd.predict(Xc_test)))
print(f"  Crowd RMSE: {rmse_c:.1f}%")
print(f"  R² Score  : {lr_crowd.score(Xc_test, yc_test):.4f}")

with open(os.path.join(SAVE_DIR, 'crowd_model.pkl'), 'wb') as f:
    pickle.dump(lr_crowd, f)
print("  ✅ Saved: crowd_model.pkl")

# ─── 3. ROUTE RECOMMENDATION — Random Forest ────────────────

print("\nTraining Route Recommendation Model (Random Forest)...")
ROUTES = ['8A','1P','90L','188','8X','224']
STOPS = ['Secunderabad','MGBS','Charminar','Ameerpet','LB Nagar',
         'Hitec City','Miyapur','Gachibowli','Uppal','Airport']

le_from = LabelEncoder().fit(STOPS)
le_to   = LabelEncoder().fit(STOPS)
le_rt   = LabelEncoder().fit(ROUTES)

from_enc = np.random.randint(0, len(STOPS), N)
to_enc   = np.random.randint(0, len(STOPS), N)
route_labels = np.random.randint(0, len(ROUTES), N)

X_rec = np.column_stack([from_enc, to_enc])
Xr_train, Xr_test, yr_train, yr_test = train_test_split(X_rec, route_labels, test_size=0.2)
rf = RandomForestClassifier(n_estimators=50, random_state=42)
rf.fit(Xr_train, yr_train)
acc = accuracy_score(yr_test, rf.predict(Xr_test))
print(f"  Route Accuracy: {acc*100:.1f}%")

with open(os.path.join(SAVE_DIR, 'route_model.pkl'), 'wb') as f:
    pickle.dump({'model': rf, 'le_from': le_from, 'le_to': le_to, 'le_route': le_rt}, f)
print("  ✅ Saved: route_model.pkl")

# ─── 4. PEAK HOUR CLASSIFIER — Decision Tree ────────────────

print("\nTraining Peak Hour Classifier (Decision Tree)...")
hour_feats = np.column_stack([
    hours_c,
    (hours_c >= 7).astype(int),
    (hours_c >= 17).astype(int),
])
peak_classes = np.where(
    ((hours_c>=7)&(hours_c<=10)), 0,
    np.where(((hours_c>=17)&(hours_c<=20)), 1,
    np.where(((hours_c>=11)&(hours_c<=16)), 2,
    np.where((hours_c>=21), 3, 4)))
)  # 0=morning peak, 1=evening peak, 2=offpeak, 3=night, 4=early morning

Xp_train, Xp_test, yp_train, yp_test = train_test_split(hour_feats, peak_classes, test_size=0.2)
dt = DecisionTreeClassifier(max_depth=5, random_state=42)
dt.fit(Xp_train, yp_train)
acc_p = accuracy_score(yp_test, dt.predict(Xp_test))
print(f"  Peak Classifier Accuracy: {acc_p*100:.1f}%")

with open(os.path.join(SAVE_DIR, 'peak_model.pkl'), 'wb') as f:
    pickle.dump(dt, f)
print("  ✅ Saved: peak_model.pkl")

print("\n🎉 All models trained and saved successfully!")
print("Model files:", os.listdir(SAVE_DIR))
