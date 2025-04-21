import redis
import json
import random
import hashlib
from datetime import datetime

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

def generate_message_key(customer_number, content):
    """Generate a unique key for a message based on customer_number and content."""
    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    return f"{customer_number}:{content_hash}"

def handle_notification(notification):
    """Handle an incoming message notification."""
    # Extract notification details
    customer_number = notification['customer_number']
    content = notification['content']
    timestamp = notification['timestamp']
    
    # Generate unique message key
    message_key = generate_message_key(customer_number, content)
    
    # Check for duplicate message
    if r.hexists('messages', message_key):
        print(f"Duplicate message from {customer_number} with content '{content}', ignoring.")
        return
    
    # Add new message to Redis with status "pending"
    message_data = {
        'content': content,
        'customer_number': customer_number,
        'timestamp': timestamp,
        'status': 'pending',
        'assigned_agent_id': None
    }
    r.hset('messages', message_key, json.dumps(message_data))
    
    # Select agent for assignment
    agent_id = select_agent(customer_number)
    
    # Assign message to the selected agent
    assign_message_to_agent(message_key, agent_id, customer_number)
    
    # Simulate streaming to Kafka
    print(f"Streaming message {message_key} to Kafka for agent {agent_id}")

def select_agent(customer_number):
    """Select an agent for the message based on session continuity or workload."""
    # Check if customer has an active session with an online agent
    if r.hexists('active_sessions', customer_number):
        agent_id = r.hget('active_sessions', customer_number).decode('utf-8')
        agent_data = json.loads(r.hget('agents', agent_id).decode('utf-8'))
        if agent_data['status'] == 'online':
            return agent_id
    
    # Select the least busy online agent
    min_count = r.zrange('online_agents', 0, 0, withscores=True)
    if not min_count:
        raise Exception("No online agents available")
    
    min_score = min_count[0][1]
    candidates = r.zrangebyscore('online_agents', min_score, min_score)
    
    # Randomly select one if multiple candidates
    selected_agent_id = random.choice(candidates).decode('utf-8')
    return selected_agent_id

def assign_message_to_agent(message_key, agent_id, customer_number):
    """Assign the message to the specified agent and update states."""
    # Retrieve message and agent data
    message_data = json.loads(r.hget('messages', message_key).decode('utf-8'))
    agent_data = json.loads(r.hget('agents', agent_id).decode('utf-8'))
    
    # Check if this is a new session for the agent
    if customer_number not in agent_data['sessions']:
        agent_data['sessions'].append(customer_number)
        agent_data['session_count'] += 1
        r.hset('agents', agent_id, json.dumps(agent_data))
        r.zadd('online_agents', {agent_id: agent_data['session_count']})
    
    # Handle reassignment if customer was previously assigned to another agent
    if r.hexists('active_sessions', customer_number):
        previous_agent_id = r.hget('active_sessions', customer_number).decode('utf-8')
        if previous_agent_id != agent_id:
            previous_agent_data = json.loads(r.hget('agents', previous_agent_id).decode('utf-8'))
            if customer_number in previous_agent_data['sessions']:
                previous_agent_data['sessions'].remove(customer_number)
                previous_agent_data['session_count'] -= 1
                r.hset('agents', previous_agent_id, json.dumps(previous_agent_data))
                if previous_agent_data['status'] == 'online':
                    r.zadd('online_agents', {previous_agent_id: previous_agent_data['session_count']})
    
    # Update active sessions and message status
    r.hset('active_sessions', customer_number, agent_id)
    message_data['status'] = 'assigned'
    message_data['assigned_agent_id'] = agent_id
    r.hset('messages', message_key, json.dumps(message_data))










import redis
import hashlib
import json

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

def generate_message_key(customer_number, content):
    """Generate a unique key for deduplication."""
    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    return f"{customer_number}:{content_hash}"

def select_agent(customer_number):
    """Select an agent, preferring the existing one if available."""
    # Check for an existing session
    if r.hexists('active_sessions', customer_number):
        agent_id = r.hget('active_sessions', customer_number).decode('utf-8')
        agent_data = json.loads(r.hget('agents', agent_id).decode('utf-8'))
        if agent_data['status'] == 'online':
            return agent_id
    
    # Fallback to least busy agent (simplified here)
    online_agents = r.hkeys('agents')  # In practice, use a sorted set for efficiency
    for agent_id in online_agents:
        agent_data = json.loads(r.hget('agents', agent_id).decode('utf-8'))
        if agent_data['status'] == 'online':
            return agent_id.decode('utf-8')
    raise Exception("No online agents available")

def handle_message(customer_number, content):
    """Process an incoming message."""
    message_key = generate_message_key(customer_number, content)
    if r.hexists('messages', message_key):
        print(f"Duplicate message from {customer_number}, ignored.")
        return
    
    # Store the message
    r.hset('messages', message_key, json.dumps({'content': content, 'status': 'pending'}))
    
    # Assign to an agent
    agent_id = select_agent(customer_number)
    r.hset('active_sessions', customer_number, agent_id)
    r.hset('messages', message_key, json.dumps({'content': content, 'status': 'assigned', 'agent': agent_id}))
    print(f"Assigned message from {customer_number} to {agent_id}")




# Example usage and testing
if __name__ == "__main__":
    # Clear Redis for testing
    r.flushdb()
    
    # Add sample agents
    def add_agent(agent_id):
        agent_data = {
            'status': 'online',
            'session_count': 0,
            'sessions': []
        }
        r.hset('agents', agent_id, json.dumps(agent_data))
        r.zadd('online_agents', {agent_id: 0})
    
    add_agent('1')
    add_agent('2')
    
    # Simulate notifications
    # Message 1: New message from customer 1234567890
    notification1 = {
        'customer_number': '1234567890',
        'content': 'Hello',
        'timestamp': str(datetime.now())
    }
    handle_notification(notification1)
    
    # Message 2: Same content from same customer (duplicate)
    notification2 = {
        'customer_number': '1234567890',
        'content': 'Hello',
        'timestamp': str(datetime.now())
    }
    handle_notification(notification2)
    
    # Message 3: New content from same customer
    notification3 = {
        'customer_number': '1234567890',
        'content': 'How are you?',
        'timestamp': str(datetime.now())
    }
    handle_notification(notification3)
    
    # Message 4: New customer
    notification4 = {
        'customer_number': '0987654321',
        'content': 'Hi there',
        'timestamp': str(datetime.now())
    }
    handle_notification(notification4)
    
    # Test agent offline scenario
    # Set agent 1 offline
    agent1_data = json.loads(r.hget('agents', '1').decode('utf-8'))
    agent1_data['status'] = 'offline'
    r.hset('agents', '1', json.dumps(agent1_data))
    r.zrem('online_agents', '1')
    
    # Message 5: From customer 1234567890, should reassign
    notification5 = {
        'customer_number': '1234567890',
        'content': 'Are you there?',
        'timestamp': str(datetime.now())
    }
    handle_notification(notification5)
    
    # Print states for verification
    print("\nMessages:")
    for key in r.hkeys('messages'):
        print(f"{key.decode('utf-8')}: {r.hget('messages', key).decode('utf-8')}")
    
    print("\nAgents:")
    for key in r.hkeys('agents'):
        print(f"{key.decode('utf-8')}: {r.hget('agents', key).decode('utf-8')}")
    
    print("\nActive Sessions:")
    for key in r.hkeys('active_sessions'):
        print(f"{key.decode('utf-8')}: {r.hget('active_sessions', key).decode('utf-8')}")