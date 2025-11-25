#!/usr/bin/env python
"""
Management script for E-Invoice application
Provides CLI commands for administrative tasks
"""
import argparse
import sys
import os
from app import app
from models import db, User


def create_admin(email, password):
    """
    Create an admin user account
    
    Args:
        email (str): Admin email address
        password (str): Admin password
    
    Returns:
        bool: True if admin created successfully, False otherwise
    """
    with app.app_context():
        # Check if user with this email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"Error: User with email '{email}' already exists.")
            print(f"  User ID: {existing_user.id}")
            print(f"  Username: {existing_user.username}")
            print(f"  Role: {existing_user.role}")
            return False
        
        # Generate username from email (part before @)
        username = email.split('@')[0]
        
        # Check if username already exists
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            # Append a number to make it unique
            counter = 1
            base_username = username
            while existing_username:
                username = f"{base_username}{counter}"
                existing_username = User.query.filter_by(username=username).first()
                counter += 1
        
        # Create admin user
        try:
            admin_user = User(
                username=username,
                email=email,
                password=password,
                role='admin',
                is_active=True
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("=" * 60)
            print("Admin user created successfully!")
            print("=" * 60)
            print(f"  Email: {email}")
            print(f"  Username: {username}")
            print(f"  Role: admin")
            print(f"  Status: active")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {str(e)}")
            return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='E-Invoice Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage.py create-admin --email admin@example.com --password securepass123
  python manage.py create-admin -e admin@example.com -p securepass123
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # create-admin command
    create_admin_parser = subparsers.add_parser(
        'create-admin',
        help='Create an admin user account'
    )
    create_admin_parser.add_argument(
        '--email', '-e',
        type=str,
        required=True,
        help='Admin email address'
    )
    create_admin_parser.add_argument(
        '--password', '-p',
        type=str,
        required=True,
        help='Admin password'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'create-admin':
        # Validate email format (basic check)
        if '@' not in args.email:
            print("Error: Invalid email format. Email must contain '@' symbol.")
            sys.exit(1)
        
        # Validate password length
        if len(args.password) < 6:
            print("Error: Password must be at least 6 characters long.")
            sys.exit(1)
        
        success = create_admin(args.email, args.password)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()

