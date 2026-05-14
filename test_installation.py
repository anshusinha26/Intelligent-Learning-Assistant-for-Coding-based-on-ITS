"""
Simple test script to verify the installation
Run this to check if all modules are working
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from src.database import Database
        print("✓ Database module imported")
        
        from src.models import User, Problem, Attempt
        print("✓ Models module imported")
        
        from src.auth import AuthService
        print("✓ Auth module imported")
        
        from src.learner_model import LearnerModel
        print("✓ Learner model module imported")
        
        from src.recommender import RecommendationEngine
        print("✓ Recommender module imported")
        
        from src.revision_scheduler import RevisionScheduler
        print("✓ Revision scheduler module imported")

        from src.judge import JudgeService
        print("✓ Judge module imported")
        
        print("\n✅ All imports successful!\n")
        return True
    except ImportError as e:
        print(f"\n❌ Import error: {e}\n")
        print("Please run: pip install -r requirements.txt")
        return False

def test_database():
    """Test database creation and basic operations"""
    print("Testing database...")
    
    try:
        from src.database import Database
        
        # Create test database
        test_db = Database(db_path="data/test.db")
        conn = test_db.get_connection()
        
        # Test table creation
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['users', 'problems', 'attempts', 'learner_metrics',
                          'recommendations', 'revision_schedule', 'submissions']
        
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        conn.close()
        
        # Clean up test database
        os.remove("data/test.db")
        
        print("✓ Database schema verified")
        print("✅ Database tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}\n")
        return False

def test_auth():
    """Test authentication system"""
    print("Testing authentication...")
    
    try:
        from src.database import Database
        from src.auth import AuthService
        
        # Create test database
        test_db = Database(db_path="data/test_auth.db")
        auth = AuthService(test_db)
        
        # Test password hashing
        password = "test123"
        hashed = auth.hash_password(password)
        assert auth.verify_password(password, hashed), "Password verification failed"
        print("✓ Password hashing works")
        
        # Test user registration
        result = auth.register_user("Test User", "test@test.com", "password123")
        assert 'access_token' in result, "Registration didn't return token"
        print("✓ User registration works")
        
        # Test login
        login_result = auth.login_user("test@test.com", "password123")
        assert 'access_token' in login_result, "Login didn't return token"
        print("✓ User login works")
        
        # Test token verification
        token = login_result['access_token']
        user = auth.get_current_user(token)
        assert user is not None, "Token verification failed"
        print("✓ Token verification works")
        
        # Clean up
        os.remove("data/test_auth.db")
        
        print("✅ Authentication tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Authentication error: {e}\n")
        if os.path.exists("data/test_auth.db"):
            os.remove("data/test_auth.db")
        return False

def main():
    print("=" * 50)
    print("Intelligent Coding Assistant - Installation Test")
    print("=" * 50)
    print()
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Database", test_database()))
    results.append(("Authentication", test_auth()))
    
    # Summary
    print("=" * 50)
    print("Test Summary:")
    print("=" * 50)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20s} {status}")
    
    print()
    
    if all(result[1] for result in results):
        print("🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Run: python load_sample_data.py")
        print("2. Run: python src/main.py")
        print("3. Open frontend/index.html in your browser")
    else:
        print("⚠️  Some tests failed. Please fix the errors above.")
        print("\nCommon fixes:")
        print("- Run: pip install -r requirements.txt")
        print("- Make sure Python 3.8+ is installed")
    
    print()

if __name__ == "__main__":
    main()
