import os
import pandas as pd
from sqlalchemy import create_engine
from ucimlrepo import fetch_ucirepo
import mysql.connector

db_password = os.environ.get("DB_PASSWORD")
if not db_password:
    raise ValueError("DB_PASSWORD environment variable not set.")

print("📦 Fetching Travel Reviews dataset from UCI...")
travel_reviews = fetch_ucirepo(id=484)
df = travel_reviews.data.features.copy()

print("🧹 Cleaning and remodeling data rows...")
if "User" in df.columns:
    df["user_id"] = df["User"].str.extract(r"(\d+)").astype(int)
    df = df.drop(columns=["User"])
else:
    df.index.name = "user_id"
    df = df.reset_index()

df.columns = (
    df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace(".", "_")
)

for col in df.select_dtypes(include=["float64", "int64"]).columns:
    if col != "user_id":
        df[col] = df[col].fillna(df[col].mean())

category_columns = [col for col in df.columns if col != "user_id"]
df_melted = pd.melt(
    df, id_vars=["user_id"], value_vars=category_columns,
    var_name="feedback_category", value_name="rating",
)

df_melted["is_satisfied"] = df_melted["rating"].apply(lambda x: 1 if x >= 3.0 else 0)

print("🔗 Connecting and writing directly to MySQL Server...")
engine = create_engine(f"mysql+pymysql://root:{db_password}@localhost:3306/new_schema")
df_melted.to_sql("user_feedback", engine, if_exists="replace", index=False)

print("🚀 Pipeline complete!")

conn = mysql.connector.connect(host='localhost', username='root', password=db_password, database='new_schema')
conn.close()
print("connection successfully connected")