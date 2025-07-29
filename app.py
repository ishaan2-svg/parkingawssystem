#!/usr/bin/env python3
"""
SmartPark Pro - Python Flask Backend
Handles JSON file operations and provides REST API for the parking system
Works with minimal AWS integration (graceful degradation)
"""

import json
import os
import uuid
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import threading
import time
import pytz  # Added for timezone support

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Configuration
CONFIG = {
    'USER_DATA_FILE': 'user_data.json',
    'PARKING_LAYOUT_FILE': 'parking_layout.json',
    'BACKUP_DIR': 'backups',
    'AWS_ENABLED': False,
    'FLOORS': 5,
    'DIVISIONS_PER_FLOOR': 10,
    'SPOTS_PER_DIVISION': 20
}

# Minimal AWS Configuration 
AWS_CONFIG = {
    'region': 'us-east-1',
    'bucket_name': 'smartpark-data'  # Just basic S3 backup
}

# Create IST timezone object
IST = pytz.timezone('Asia/Kolkata')

class SmartParkBackend:
    def __init__(self):
        self.ensure_directories()
        self.ensure_json_files()
        self.s3 = None
        self.aws_status = "disconnected"
        self.check_aws_basic()
        
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(CONFIG['BACKUP_DIR'], exist_ok=True)
        
    def ensure_json_files(self):
        """Create JSON files if they don't exist"""
        if not os.path.exists(CONFIG['USER_DATA_FILE']):
            self.create_initial_user_data()
            
        if not os.path.exists(CONFIG['PARKING_LAYOUT_FILE']):
            self.create_initial_parking_layout()
            
    def check_aws_basic(self):
        """Basic AWS check - don't expect much"""
        try:
            self.s3 = boto3.client('s3', region_name=AWS_CONFIG['region'])
            # Just try a simple operation
            self.s3.list_buckets()
            CONFIG['AWS_ENABLED'] = True
            self.aws_status = "connected"
            print("✅ Basic AWS S3 available")
        except Exception as e:
            print(f"⚠️  AWS not available: {str(e)[:50]}...")
            print("📁 Running in local mode")
            CONFIG['AWS_ENABLED'] = False
            self.aws_status = "unavailable"
            
    def simple_aws_backup(self, filename, data):
        """Simple AWS backup - just upload to S3 if available"""
        if not CONFIG['AWS_ENABLED'] or not self.s3:
            return False
            
        try:
            self.s3.put_object(
                Bucket=AWS_CONFIG['bucket_name'],
                Key=f"backups/{filename}",
                Body=json.dumps(data, indent=2)
            )
            return True
        except Exception as e:
            print(f"⚠️  AWS backup failed: {str(e)[:50]}...")
            return False
            
    def create_initial_user_data(self):
        """Create initial user data file"""
        initial_data = {
            "version": "1.0",
            "created": datetime.now(IST).isoformat(),
            "lastModified": datetime.now(IST).isoformat(),
            "users": [
                {
                    "id": f"USER_{int(time.time())}",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "9876543210",
                    "vehicleId": "KA-01-HH-1234",
                    "password": "demo123",
                    "createdAt": datetime.now(IST).isoformat(),
                    "totalBookings": 0,
                    "totalSpent": 0,
                    "status": "active",
                    "bookingHistory": []
                },
                {
                    "id": f"USER_{int(time.time()) + 1}",
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "phone": "9876543211",
                    "vehicleId": "KA-02-BB-5678",
                    "password": "demo123",
                    "createdAt": datetime.now(IST).isoformat(),
                    "totalBookings": 0,
                    "totalSpent": 0,
                    "status": "active",
                    "bookingHistory": []
                }
            ]
        }
        
        self.save_json_file(CONFIG['USER_DATA_FILE'], initial_data)
        print(f"📁 Created initial user data: {CONFIG['USER_DATA_FILE']}")
        
    def create_initial_parking_layout(self):
        """Create initial parking layout file"""
        layout = {
            "version": "1.0",
            "created": datetime.now(IST).isoformat(),
            "lastModified": datetime.now(IST).isoformat(),
            "totalFloors": CONFIG['FLOORS'],
            "divisionsPerFloor": CONFIG['DIVISIONS_PER_FLOOR'],
            "spotsPerDivision": CONFIG['SPOTS_PER_DIVISION'],
            "floors": {},
            "activeBookings": [],
            "bookingHistory": []
        }
        
        # Generate parking spots
        for floor in range(1, CONFIG['FLOORS'] + 1):
            layout["floors"][str(floor)] = {}
            
            for division in range(1, CONFIG['DIVISIONS_PER_FLOOR'] + 1):
                layout["floors"][str(floor)][str(division)] = {}
                
                for spot in range(1, CONFIG['SPOTS_PER_DIVISION'] + 1):
                    spot_id = f"{floor}-{division:02d}-{spot:02d}"
                    layout["floors"][str(floor)][str(division)][str(spot)] = {
                        "id": spot_id,
                        "floor": floor,
                        "division": division,
                        "spotNumber": spot,
                        "available": random.random() > 0.3,
                        "bookedBy": None,
                        "bookedAt": None,
                        "bookedUntil": None,
                        "bookingId": None,
                        "lastSensorUpdate": datetime.now(IST).isoformat(),
                        "sensorStatus": "active",
                        "distanceFromEntrance": (division - 1) * 20 + (spot - 1) * 2,
                        "preferredEntrance": "main" if division <= 5 else "rear"
                    }
        
        self.save_json_file(CONFIG['PARKING_LAYOUT_FILE'], layout)
        print(f"🚗 Created initial parking layout: {CONFIG['PARKING_LAYOUT_FILE']}")
        
    def load_json_file(self, filename):
        """Load JSON file with error handling"""
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Error loading {filename}: {e}")
            return None
            
    def save_json_file(self, filename, data):
        """Save JSON file with optional AWS backup"""
        try:
            data['lastModified'] = datetime.now(IST).isoformat()
            
            # Create backup
            if os.path.exists(filename):
                backup_name = f"{CONFIG['BACKUP_DIR']}/{filename}.{int(time.time())}.bak"
                os.rename(filename, backup_name)
            
            # Save new file
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
                
            # Try simple AWS backup (don't expect much)
            aws_backed_up = self.simple_aws_backup(filename, data)
            if aws_backed_up:
                print(f"☁️  Backed up {filename} to AWS")
                
            return True
            
        except Exception as e:
            print(f"❌ Error saving {filename}: {e}")
            return False

# Initialize backend
backend = SmartParkBackend()

def parse_booking_time(time_str):
    """Parse booking time string and convert to IST datetime"""
    try:
        # Parse the datetime string
        dt = datetime.fromisoformat(time_str)
        
        # If the datetime is naive (no timezone), localize to IST
        if dt.tzinfo is None:
            dt = IST.localize(dt)
        else:
            # Convert to IST if it has timezone info
            dt = dt.astimezone(IST)
            
        return dt
    except Exception as e:
        print(f"⚠️  Error parsing time {time_str}: {e}")
        return datetime.now(IST)

# Serve static files and main page
@app.route('/')
def serve_homepage():
    """Serve the main HTML file"""
    try:
        if os.path.exists('smartpark.html'):
            # Fix: Open with UTF-8 encoding
            with open('smartpark.html', 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>SmartPark Pro Backend</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .error { color: #ff6b6b; }
                    .info { color: #667eea; }
                </style>
            </head>
            <body>
                <h1>🚗 SmartPark Pro Backend</h1>
                <p class="error">❌ smartpark.html not found</p>
                <p class="info">📁 Place smartpark.html in the same directory as app.py</p>
                <p class="info">🌐 API is running at: <a href="/api/health">/api/health</a></p>
            </body>
            </html>
            """
    except Exception as e:
        return f"Error serving homepage: {e}", 500

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    try:
        return send_from_directory('.', filename)
    except:
        return "File not found", 404

# Simple API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(IST).isoformat(),
        'aws_available': CONFIG['AWS_ENABLED'],
        'aws_status': backend.aws_status,
        'files_exist': {
            'users': os.path.exists(CONFIG['USER_DATA_FILE']),
            'layout': os.path.exists(CONFIG['PARKING_LAYOUT_FILE'])
        }
    })

@app.route('/api/users', methods=['GET', 'POST'])
def handle_users():
    """Handle user operations"""
    if request.method == 'GET':
        data = backend.load_json_file(CONFIG['USER_DATA_FILE'])
        if data:
            return jsonify({'success': True, 'users': data['users']})
        return jsonify({'success': False, 'error': 'Failed to load users'})
        
    elif request.method == 'POST':
        user_data = request.json
        data = backend.load_json_file(CONFIG['USER_DATA_FILE'])
        
        if not data:
            return jsonify({'success': False, 'error': 'Failed to load user data'})
            
        # Check if user exists
        existing = next((u for u in data['users'] if u['vehicleId'] == user_data['vehicleId']), None)
        if existing:
            return jsonify({'success': False, 'error': 'User already exists'})
            
        # Create new user
        new_user = {
            'id': f"USER_{int(time.time())}_{uuid.uuid4().hex[:6].upper()}",
            'name': user_data['name'],
            'email': user_data['email'],
            'phone': user_data['phone'],
            'vehicleId': user_data['vehicleId'],
            'password': user_data['password'],
            'createdAt': datetime.now(IST).isoformat(),
            'lastLogin': datetime.now(IST).isoformat(),
            'totalBookings': 0,
            'totalSpent': 0,
            'status': 'active',
            'bookingHistory': []
        }
        
        data['users'].append(new_user)
        
        if backend.save_json_file(CONFIG['USER_DATA_FILE'], data):
            return jsonify({'success': True, 'user': new_user})
        
        return jsonify({'success': False, 'error': 'Failed to create user'})

@app.route('/api/auth', methods=['POST'])
def authenticate():
    """Authenticate user"""
    credentials = request.json
    data = backend.load_json_file(CONFIG['USER_DATA_FILE'])
    
    if not data:
        return jsonify({'success': False, 'error': 'Failed to load user data'})
        
    user = next(
        (u for u in data['users'] if u['vehicleId'] == credentials['vehicleId'] and u['password'] == credentials['password']),
        None
    )
    
    if user:
        user['lastLogin'] = datetime.now(IST).isoformat()
        backend.save_json_file(CONFIG['USER_DATA_FILE'], data)
        return jsonify({'success': True, 'user': user})
    
    return jsonify({'success': False, 'error': 'Invalid credentials'})

@app.route('/api/parking-layout', methods=['GET', 'PUT'])
def handle_parking_layout():
    """Handle parking layout operations"""
    if request.method == 'GET':
        data = backend.load_json_file(CONFIG['PARKING_LAYOUT_FILE'])
        if data:
            return jsonify({'success': True, 'layout': data})
        return jsonify({'success': False, 'error': 'Failed to load parking layout'})
        
    elif request.method == 'PUT':
        layout_data = request.json
        if backend.save_json_file(CONFIG['PARKING_LAYOUT_FILE'], layout_data):
            return jsonify({'success': True, 'layout': layout_data})
        return jsonify({'success': False, 'error': 'Failed to update layout'})

@app.route('/api/bookings', methods=['GET', 'POST'])
def handle_bookings():
    """Handle booking operations"""
    if request.method == 'GET':
        user_id = request.args.get('userId')
        data = backend.load_json_file(CONFIG['USER_DATA_FILE'])
        
        if not data:
            return jsonify({'success': False, 'error': 'Failed to load user data'})
            
        if user_id:
            user = next((u for u in data['users'] if u['id'] == user_id), None)
            if user:
                return jsonify({'success': True, 'bookings': user.get('bookingHistory', [])})
            return jsonify({'success': False, 'error': 'User not found'})
        
        # Return all bookings
        all_bookings = []
        for user in data['users']:
            all_bookings.extend(user.get('bookingHistory', []))
        
        return jsonify({'success': True, 'bookings': all_bookings})
        
    elif request.method == 'POST':
        booking_data = request.json
        
        # Load parking layout
        layout = backend.load_json_file(CONFIG['PARKING_LAYOUT_FILE'])
        if not layout:
            return jsonify({'success': False, 'error': 'Failed to load parking layout'})
            
        # Parse spot location
        spot_parts = booking_data['spotId'].split('-')
        floor, division, spot = int(spot_parts[0]), int(spot_parts[1]), int(spot_parts[2])
        
        # Check spot availability
        spot_data = layout['floors'][str(floor)][str(division)][str(spot)]
        if not spot_data['available']:
            return jsonify({'success': False, 'error': 'Spot no longer available'})
            
        # Create booking
        booking_record = {
            'id': f"BOOK_{int(time.time())}_{uuid.uuid4().hex[:6].upper()}",
            'spotId': booking_data['spotId'],
            'userId': booking_data['userId'],
            'startTime': booking_data['startTime'],
            'endTime': booking_data['endTime'],
            'duration': booking_data['duration'],
            'cost': booking_data['cost'],
            'status': 'active',
            'createdAt': datetime.now(IST).isoformat(),
            'floor': floor,
            'division': division,
            'spotNumber': spot
        }
        
        # Update spot
        spot_data['available'] = False
        spot_data['bookedBy'] = booking_data['userId']
        spot_data['bookedAt'] = booking_data['startTime']
        spot_data['bookedUntil'] = booking_data['endTime']
        spot_data['bookingId'] = booking_record['id']
        spot_data['lastSensorUpdate'] = datetime.now(IST).isoformat()
        spot_data['sensorStatus'] = "occupied"  # NEW: Add sensor status
        
        # Add to active bookings
        layout['activeBookings'].append(booking_record)
        
        # NEW: Also add to booking history
        if 'bookingHistory' not in layout:
            layout['bookingHistory'] = []
        layout['bookingHistory'].append(booking_record)
        
        # Save layout
        if not backend.save_json_file(CONFIG['PARKING_LAYOUT_FILE'], layout):
            return jsonify({'success': False, 'error': 'Failed to update parking layout'})
            
        # Update user history
        user_data = backend.load_json_file(CONFIG['USER_DATA_FILE'])
        if user_data:
            user = next((u for u in user_data['users'] if u['id'] == booking_data['userId']), None)
            if user:
                if 'bookingHistory' not in user:
                    user['bookingHistory'] = []
                user['bookingHistory'].append(booking_record)
                user['totalBookings'] = user.get('totalBookings', 0) + 1
                user['totalSpent'] = user.get('totalSpent', 0) + booking_data['cost']
                backend.save_json_file(CONFIG['USER_DATA_FILE'], user_data)
        
        return jsonify({'success': True, 'booking': booking_record})

@app.route('/api/spots/closest', methods=['GET'])
def find_closest_spot():
    """Find closest available spot"""
    layout = backend.load_json_file(CONFIG['PARKING_LAYOUT_FILE'])
    if not layout:
        return jsonify({'success': False, 'error': 'Failed to load parking layout'})
        
    closest_spot = None
    min_distance = float('inf')
    
    for floor in range(1, CONFIG['FLOORS'] + 1):
        for division in range(1, CONFIG['DIVISIONS_PER_FLOOR'] + 1):
            for spot in range(1, CONFIG['SPOTS_PER_DIVISION'] + 1):
                spot_data = layout['floors'][str(floor)][str(division)][str(spot)]
                
                if spot_data['available']:
                    distance = abs(floor - 1) * 50 + abs(division - 5) * 10 + abs(spot - 10) * 1
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_spot = {
                            **spot_data,
                            'floor': floor,
                            'division': division,
                            'position': spot,
                            'distance': distance,
                            'closestEntrance': 'main' if division <= 5 else 'rear'
                        }
    
    if closest_spot:
        return jsonify({'success': True, 'spot': closest_spot})
    
    return jsonify({'success': False, 'error': 'No available spots found'})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get basic parking statistics"""
    layout = backend.load_json_file(CONFIG['PARKING_LAYOUT_FILE'])
    user_data = backend.load_json_file(CONFIG['USER_DATA_FILE'])
    
    if not layout or not user_data:
        return jsonify({'success': False, 'error': 'Failed to load data'})
        
    total_spots = available_spots = occupied_spots = 0
    
    for floor in layout['floors'].values():
        for division in floor.values():
            for spot_data in division.values():
                total_spots += 1
                if spot_data['available']:
                    available_spots += 1
                else:
                    occupied_spots += 1
    
    occupancy_rate = (occupied_spots / total_spots) * 100 if total_spots > 0 else 0
    
    stats = {
        'totalSpots': total_spots,
        'availableSpots': available_spots,
        'occupiedSpots': occupied_spots,
        'occupancyRate': round(occupancy_rate, 2),
        'totalUsers': len(user_data['users']),
        'activeBookings': len(layout.get('activeBookings', [])),
        'totalBookings': len(layout.get('bookingHistory', [])),
        'lastUpdated': datetime.now(IST).isoformat(),
        'aws_available': CONFIG['AWS_ENABLED']
    }
    
    return jsonify({'success': True, 'stats': stats})

def expire_bookings():
    """Background task to automatically expire bookings"""
    while True:
        try:
            layout = backend.load_json_file(CONFIG['PARKING_LAYOUT_FILE'])
            if layout and 'activeBookings' in layout:
                current_time = datetime.now(IST)  # Use IST instead of UTC
                
                print(f"🕒 Checking {len(layout['activeBookings'])} active bookings at {current_time}")
                
                expired_bookings = []
                
                for booking in layout['activeBookings']:
                    try:
                        # Parse the booking end time properly
                        booking_end_time = parse_booking_time(booking['endTime'])
                        
                        # Debug output
                        time_remaining = booking_end_time - current_time
                        print(f"📍 Booking {booking['id'][:8]}...: ends at {booking_end_time}, time remaining: {time_remaining}")
                        
                        # Only expire if the booking is actually past its end time
                        if current_time > booking_end_time:
                            expired_bookings.append(booking)
                            print(f"⏰ Booking {booking['id'][:8]}... is expired!")
                        
                    except Exception as e:
                        print(f"⚠️  Error processing booking {booking.get('id', 'unknown')}: {e}")
                        continue
                
                if expired_bookings:
                    for booking in expired_bookings:
                        try:
                            # Free the spot
                            floor = str(booking['floor'])
                            division = str(booking['division'])
                            spot = str(booking['spotNumber'])
                            
                            spot_data = layout['floors'][floor][division][spot]
                            spot_data['available'] = True
                            spot_data['bookedBy'] = None
                            spot_data['bookedAt'] = None
                            spot_data['bookedUntil'] = None
                            spot_data['bookingId'] = None
                            spot_data['lastSensorUpdate'] = datetime.now(IST).isoformat()
                            
                            # Move to history
                            booking['status'] = 'expired'
                            booking['completedAt'] = datetime.now(IST).isoformat()
                            layout['bookingHistory'].append(booking)
                            
                        except Exception as e:
                            print(f"⚠️  Error expiring booking {booking.get('id', 'unknown')}: {e}")
                    
                    # Remove expired bookings from active list
                    layout['activeBookings'] = [
                        b for b in layout['activeBookings'] 
                        if b not in expired_bookings
                    ]
                    
                    backend.save_json_file(CONFIG['PARKING_LAYOUT_FILE'], layout)
                    print(f"✅ Successfully expired {len(expired_bookings)} bookings")
                else:
                    print("✅ No bookings to expire")
                    
        except Exception as e:
            print(f"❌ Error in expire_bookings: {e}")
            
        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    # Start background task
    expiry_thread = threading.Thread(target=expire_bookings, daemon=True)
    expiry_thread.start()
    
    print("🚀 SmartPark Pro Backend Starting...")
    print(f"📁 Files: {CONFIG['USER_DATA_FILE']}, {CONFIG['PARKING_LAYOUT_FILE']}")
    print(f"☁️  AWS: {'Available' if CONFIG['AWS_ENABLED'] else 'Not Available'}")
    print("🌐 Server running on http://localhost:8000")
    print("📋 Basic API endpoints available")
    
    if not CONFIG['AWS_ENABLED']:
        print("⚠️  Running in local mode - limited AWS integration")
    
    app.run(host='0.0.0.0', port=8000, debug=True)