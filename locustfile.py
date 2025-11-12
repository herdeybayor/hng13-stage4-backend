"""
Load Testing Configuration for Distributed Notification System

Usage:
    # Run with UI
    locust -f locustfile.py --host=http://localhost:8000

    # Run headless
    locust -f locustfile.py --host=http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 2m --headless

    # Run with specific number of users
    locust -f locustfile.py --host=http://localhost:8000 -u 1000 -r 50
"""

from locust import HttpUser, task, between, events
import json
import random
import uuid
from datetime import datetime


class NotificationUser(HttpUser):
    """
    Simulates a user sending notifications through the API
    """
    
    # Wait time between tasks (in seconds)
    wait_time = between(1, 3)
    
    # Store created resources for later use
    user_ids = []
    template_codes = []
    notification_ids = []
    
    def on_start(self):
        """
        Called when a simulated user starts.
        Creates test user and templates.
        """
        # Create a test user
        user_data = {
            "name": f"Test User {uuid.uuid4().hex[:8]}",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPass123!",
            "preferences": {
                "email": True,
                "push": True
            }
        }
        
        response = self.client.post("/api/v1/users/", json=user_data)
        if response.status_code == 201:
            data = response.json()
            if data.get("success") and data.get("data"):
                user_id = data["data"]["id"]
                self.user_ids.append(user_id)
                print(f"Created user: {user_id}")
        
        # Create a test template
        template_data = {
            "code": f"test_template_{uuid.uuid4().hex[:8]}",
            "name": "Load Test Template",
            "description": "Template for load testing",
            "content": "<html><body>Hello {{name}}! Your code is {{code}}.</body></html>",
            "language": "en"
        }
        
        response = self.client.post("/api/v1/templates/", json=template_data)
        if response.status_code == 201:
            data = response.json()
            if data.get("success") and data.get("data"):
                template_code = data["data"]["code"]
                self.template_codes.append(template_code)
                print(f"Created template: {template_code}")
    
    @task(10)
    def create_email_notification(self):
        """
        Create an email notification (highest weight)
        """
        if not self.user_ids or not self.template_codes:
            return
        
        notification_data = {
            "notification_type": "email",
            "user_id": random.choice(self.user_ids),
            "template_code": random.choice(self.template_codes),
            "variables": {
                "name": f"User {random.randint(1000, 9999)}",
                "code": f"CODE-{random.randint(100000, 999999)}",
                "subject": "Load Test Notification"
            },
            "request_id": f"req_{uuid.uuid4().hex}",
            "priority": random.randint(1, 10),
            "metadata": {
                "test": "load_test",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        with self.client.post(
            "/api/v1/notifications/",
            json=notification_data,
            catch_response=True,
            name="/api/v1/notifications/ [email]"
        ) as response:
            if response.status_code == 202:
                data = response.json()
                if data.get("success") and data.get("data"):
                    notification_id = data["data"]["notification_id"]
                    self.notification_ids.append(notification_id)
                    response.success()
                else:
                    response.failure(f"Invalid response: {data}")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(5)
    def create_push_notification(self):
        """
        Create a push notification (medium weight)
        """
        if not self.user_ids or not self.template_codes:
            return
        
        notification_data = {
            "notification_type": "push",
            "user_id": random.choice(self.user_ids),
            "template_code": random.choice(self.template_codes),
            "variables": {
                "title": f"Test Notification {random.randint(1, 1000)}",
                "body": "This is a load test notification",
                "icon": "https://example.com/icon.png",
                "link": "https://example.com/details"
            },
            "request_id": f"req_{uuid.uuid4().hex}",
            "priority": random.randint(1, 10)
        }
        
        with self.client.post(
            "/api/v1/notifications/",
            json=notification_data,
            catch_response=True,
            name="/api/v1/notifications/ [push]"
        ) as response:
            if response.status_code == 202:
                data = response.json()
                if data.get("success"):
                    response.success()
                else:
                    response.failure(f"Invalid response: {data}")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(3)
    def check_notification_status(self):
        """
        Check status of a previously created notification
        """
        if not self.notification_ids:
            return
        
        notification_id = random.choice(self.notification_ids)
        
        with self.client.get(
            f"/api/v1/notifications/{notification_id}",
            catch_response=True,
            name="/api/v1/notifications/{id}"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    response.success()
                else:
                    response.failure(f"Invalid response: {data}")
            elif response.status_code == 404:
                response.success()  # Not found is acceptable during load test
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(2)
    def get_user_details(self):
        """
        Fetch user details
        """
        if not self.user_ids:
            return
        
        user_id = random.choice(self.user_ids)
        
        with self.client.get(
            f"/api/v1/users/{user_id}",
            catch_response=True,
            name="/api/v1/users/{id}"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    response.success()
                else:
                    response.failure(f"Invalid response: {data}")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(2)
    def get_template_details(self):
        """
        Fetch template details
        """
        if not self.template_codes:
            return
        
        template_code = random.choice(self.template_codes)
        
        with self.client.get(
            f"/api/v1/templates/{template_code}",
            catch_response=True,
            name="/api/v1/templates/{code}"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data"):
                    response.success()
                else:
                    response.failure(f"Invalid response: {data}")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """
        Check API Gateway health
        """
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure(f"Unhealthy: {data}")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(1)
    def test_idempotency(self):
        """
        Test idempotency by sending duplicate request_id
        """
        if not self.user_ids or not self.template_codes:
            return
        
        request_id = f"idempotency_test_{uuid.uuid4().hex[:8]}"
        
        notification_data = {
            "notification_type": "email",
            "user_id": random.choice(self.user_ids),
            "template_code": random.choice(self.template_codes),
            "variables": {
                "name": "Idempotency Test",
                "subject": "Test"
            },
            "request_id": request_id,
            "priority": 5
        }
        
        # Send first request
        response1 = self.client.post("/api/v1/notifications/", json=notification_data)
        
        # Send duplicate request
        with self.client.post(
            "/api/v1/notifications/",
            json=notification_data,
            catch_response=True,
            name="/api/v1/notifications/ [idempotency]"
        ) as response2:
            if response1.status_code == 202 and response2.status_code == 202:
                data1 = response1.json()
                data2 = response2.json()
                
                # Both should succeed and return same notification_id
                if (data1.get("data", {}).get("notification_id") == 
                    data2.get("data", {}).get("notification_id")):
                    response2.success()
                else:
                    response2.failure("Idempotency check failed")
            else:
                response2.failure(f"Status: {response2.status_code}")


class AdminUser(HttpUser):
    """
    Simulates admin operations (lower frequency)
    """
    
    wait_time = between(5, 15)
    
    @task
    def list_users(self):
        """List users with pagination"""
        params = {
            "page": random.randint(1, 5),
            "limit": random.choice([10, 20, 50])
        }
        
        with self.client.get(
            "/api/v1/users/",
            params=params,
            catch_response=True,
            name="/api/v1/users/ [list]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "meta" in data:
                    response.success()
                else:
                    response.failure(f"Invalid response: {data}")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task
    def list_templates(self):
        """List templates with pagination"""
        params = {
            "page": random.randint(1, 5),
            "limit": random.choice([10, 20, 50])
        }
        
        with self.client.get(
            "/api/v1/templates/",
            params=params,
            catch_response=True,
            name="/api/v1/templates/ [list]"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    response.success()
                else:
                    response.failure(f"Invalid response: {data}")
            else:
                response.failure(f"Status: {response.status_code}")


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("Load test starting...")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("\nLoad test completed!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"Requests per second: {environment.stats.total.total_rps:.2f}")
    
    # Check if performance targets are met
    avg_response_time = environment.stats.total.avg_response_time
    failure_rate = environment.stats.total.fail_ratio
    
    print("\n" + "="*50)
    print("Performance Target Check:")
    print("="*50)
    
    if avg_response_time < 100:
        print(f"✅ Avg Response Time: {avg_response_time:.2f}ms (Target: <100ms)")
    else:
        print(f"❌ Avg Response Time: {avg_response_time:.2f}ms (Target: <100ms)")
    
    if failure_rate < 0.005:  # 0.5%
        print(f"✅ Failure Rate: {failure_rate*100:.2f}% (Target: <0.5%)")
    else:
        print(f"❌ Failure Rate: {failure_rate*100:.2f}% (Target: <0.5%)")
    
    if environment.stats.total.total_rps >= 16.67:  # 1000/min = 16.67/sec
        print(f"✅ RPS: {environment.stats.total.total_rps:.2f} (Target: >16.67)")
    else:
        print(f"❌ RPS: {environment.stats.total.total_rps:.2f} (Target: >16.67)")
    print("="*50)


# Custom shape for ramping load
from locust import LoadTestShape

class StepLoadShape(LoadTestShape):
    """
    A step load shape that gradually increases load
    
    Step 1: 100 users for 60 seconds
    Step 2: 200 users for 60 seconds
    Step 3: 500 users for 60 seconds
    Step 4: 1000 users for 60 seconds
    """
    
    step_time = 60
    step_load = 100
    spawn_rate = 20
    time_limit = 240
    
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time < self.time_limit:
            current_step = run_time // self.step_time
            user_count = (current_step + 1) * self.step_load
            return (user_count, self.spawn_rate)
        
        return None


# To use the custom shape, run:
# locust -f locustfile.py --host=http://localhost:8000 --headless

