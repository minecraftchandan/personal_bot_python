import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB with optimized settings"""
        try:
            self.client = AsyncIOMotorClient(
                os.getenv('MONGO_URI'),
                maxPoolSize=10,
                minPoolSize=1,
                maxIdleTimeMS=30000,
                waitQueueTimeoutMS=5000
            )
            self.db = self.client.pogbot
            print("✅ Connected to MongoDB (optimized)")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("🔌 MongoDB connection closed")
    
    def get_collection(self, collection_name):
        """Get a collection from the database"""
        if self.db is None:
            raise Exception("Database not connected")
        return self.db[collection_name]

# Global MongoDB instance
mongodb = MongoDB()