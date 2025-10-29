"""
HOA Accounting System - Performance Testing with Locust

This file defines user behaviors and load testing scenarios for the HOA system.

Usage:
    # Web UI
    locust -f locustfile.py --host=http://localhost:8009

    # Headless (100 users, 10/sec spawn rate, 5 min duration)
    locust -f locustfile.py --host=http://localhost:8009 --users 100 --spawn-rate 10 --run-time 5m --headless

    # Generate HTML report
    locust -f locustfile.py --host=http://localhost:8009 --users 100 --spawn-rate 10 --run-time 5m --headless --html=report.html
"""

from locust import HttpUser, task, between, SequentialTaskSet
import random
import json
from datetime import date, timedelta


class AuthenticatedUser(HttpUser):
    """Base user class with authentication"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    token = None
    tenant_id = None

    def on_start(self):
        """Login and get JWT token when user starts"""
        self.login()

    def login(self):
        """Authenticate and get JWT token"""
        response = self.client.post("/api/v1/token/", json={
            "username": "testuser",
            "password": "testpass123"
        }, name="Login")

        if response.status_code == 200:
            self.token = response.json()["access"]
            self.client.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            print(f"Login failed: {response.status_code} - {response.text}")


class DashboardUser(AuthenticatedUser):
    """User focused on dashboard and reporting"""

    @task(10)  # Weight 10 - most common action
    def view_dashboard(self):
        """View dashboard metrics"""
        self.client.get("/api/v1/dashboard/metrics/", name="Dashboard")

    @task(5)
    def view_owners(self):
        """List all owners"""
        self.client.get("/api/v1/owners/", name="Owners List")

    @task(3)
    def view_owner_detail(self):
        """View specific owner details"""
        # Simulate viewing a random owner
        owner_id = random.randint(1, 100)
        self.client.get(f"/api/v1/owners/{owner_id}/", name="Owner Detail")

    @task(2)
    def ar_aging_report(self):
        """Generate AR aging report"""
        self.client.get("/api/v1/owners/ar-aging/", name="AR Aging Report")

    @task(1)
    def delinquency_summary(self):
        """View delinquency summary"""
        self.client.get("/api/v1/delinquency-status/summary/", name="Delinquency Summary")


class InvoicingUser(AuthenticatedUser):
    """User focused on invoicing and payments"""

    @task(8)
    def list_invoices(self):
        """List invoices with pagination"""
        page = random.randint(1, 10)
        self.client.get(f"/api/v1/invoices/?page={page}", name="Invoices List")

    @task(4)
    def view_invoice_detail(self):
        """View specific invoice"""
        # Simulate viewing a random invoice
        invoice_id = random.randint(1, 1000)
        self.client.get(f"/api/v1/invoices/{invoice_id}/", name="Invoice Detail")

    @task(3)
    def list_payments(self):
        """List payments"""
        self.client.get("/api/v1/payments/", name="Payments List")

    @task(2)
    def create_invoice(self):
        """Create a new invoice"""
        invoice_data = {
            "owner": 1,
            "unit": 1,
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=30)),
            "invoice_type": "ASSESSMENT",
            "subtotal": "250.00",
            "total_amount": "250.00",
            "description": "Monthly assessment"
        }
        self.client.post("/api/v1/invoices/", json=invoice_data, name="Create Invoice")

    @task(1)
    def record_payment(self):
        """Record a payment"""
        payment_data = {
            "owner": 1,
            "payment_date": str(date.today()),
            "amount": "250.00",
            "payment_method": "CHECK",
            "reference_number": f"CHK{random.randint(1000, 9999)}"
        }
        self.client.post("/api/v1/payments/", json=payment_data, name="Record Payment")


class BankReconciliationUser(AuthenticatedUser):
    """User focused on bank reconciliation"""

    @task(5)
    def list_bank_statements(self):
        """List bank statements"""
        self.client.get("/api/v1/bank-statements/", name="Bank Statements List")

    @task(3)
    def view_unmatched_transactions(self):
        """View unmatched transactions"""
        self.client.get("/api/v1/bank-transactions/?status=unmatched",
                       name="Unmatched Transactions")

    @task(2)
    def view_match_suggestions(self):
        """Get auto-match suggestions"""
        self.client.get("/api/v1/match-results/?was_accepted=false",
                       name="Match Suggestions")

    @task(1)
    def accept_match(self):
        """Accept a match suggestion"""
        match_id = random.randint(1, 100)
        self.client.post(f"/api/v1/match-results/{match_id}/accept/",
                        name="Accept Match")


class AdvancedFeaturesUser(AuthenticatedUser):
    """User testing Sprint 17-20 features"""

    @task(4)
    def view_violations(self):
        """List violations"""
        self.client.get("/api/v1/violations/", name="Violations List")

    @task(3)
    def view_delinquency_status(self):
        """View delinquency dashboard"""
        self.client.get("/api/v1/delinquency-status/", name="Delinquency Status")

    @task(2)
    def view_board_packets(self):
        """List board packets"""
        self.client.get("/api/v1/board-packets/", name="Board Packets")

    @task(2)
    def view_late_fee_rules(self):
        """View late fee rules"""
        self.client.get("/api/v1/late-fee-rules/", name="Late Fee Rules")

    @task(1)
    def view_match_statistics(self):
        """View matching statistics"""
        self.client.get("/api/v1/match-statistics/", name="Match Statistics")


class ReportingUser(AuthenticatedUser):
    """User focused on reports and analytics"""

    @task(5)
    def budget_variance(self):
        """View budget vs actual"""
        self.client.get("/api/v1/budgets/1/variance/", name="Budget Variance")

    @task(4)
    def owner_ledger(self):
        """View owner ledger"""
        owner_id = random.randint(1, 100)
        self.client.get(f"/api/v1/owners/{owner_id}/ledger/", name="Owner Ledger")

    @task(3)
    def journal_entries(self):
        """List journal entries"""
        self.client.get("/api/v1/journal-entries/?page=1", name="Journal Entries")

    @task(2)
    def reserve_projection(self):
        """View reserve fund projection"""
        self.client.get("/api/v1/reserve-studies/1/projection/",
                       name="Reserve Projection")


# Sequential task set for realistic user journey
class TypicalUserJourney(SequentialTaskSet):
    """Simulates a typical user session with realistic flow"""

    @task
    def step_1_login_and_dashboard(self):
        """Step 1: User logs in and views dashboard"""
        self.client.get("/api/v1/dashboard/metrics/", name="Journey: Dashboard")

    @task
    def step_2_check_owners(self):
        """Step 2: Check list of owners"""
        self.client.get("/api/v1/owners/", name="Journey: Owners")

    @task
    def step_3_view_invoices(self):
        """Step 3: Review invoices"""
        self.client.get("/api/v1/invoices/", name="Journey: Invoices")

    @task
    def step_4_check_payments(self):
        """Step 4: Check recent payments"""
        self.client.get("/api/v1/payments/", name="Journey: Payments")

    @task
    def step_5_generate_report(self):
        """Step 5: Generate AR aging report"""
        self.client.get("/api/v1/owners/ar-aging/", name="Journey: Report")


class RealisticUser(AuthenticatedUser):
    """User with realistic behavior patterns"""

    tasks = [TypicalUserJourney]
    wait_time = between(2, 5)  # More realistic wait time


# Performance test scenarios
class SpikeTestUser(AuthenticatedUser):
    """User for spike testing - rapid requests"""

    wait_time = between(0.1, 0.5)  # Very short wait time

    @task
    def rapid_dashboard_access(self):
        """Rapidly access dashboard"""
        self.client.get("/api/v1/dashboard/metrics/")


class StressTestUser(AuthenticatedUser):
    """User for stress testing - heavy operations"""

    wait_time = between(0.5, 1)

    @task(3)
    def heavy_report(self):
        """Generate heavy reports"""
        self.client.get("/api/v1/owners/ar-aging/")

    @task(2)
    def large_list(self):
        """Fetch large lists"""
        self.client.get("/api/v1/journal-entries/?page_size=100")

    @task(1)
    def complex_query(self):
        """Execute complex queries"""
        self.client.get("/api/v1/invoices/?status=overdue&page_size=50")


# Custom events for more detailed metrics
from locust import events

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Fired when test starts"""
    print("\n" + "="*50)
    print("Performance Test Starting")
    print("="*50 + "\n")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Fired when test stops"""
    print("\n" + "="*50)
    print("Performance Test Complete")
    print("="*50)
    print("\nCheck report.html for detailed results")
    print("\n")


# Shape classes for custom load patterns
from locust import LoadTestShape

class StepLoadShape(LoadTestShape):
    """
    Load pattern that steps up users in stages

    Stage 1: 0-60s = 10 users
    Stage 2: 60-120s = 25 users
    Stage 3: 120-180s = 50 users
    Stage 4: 180-240s = 100 users
    """

    step_time = 60
    step_load = 10
    spawn_rate = 2
    time_limit = 240

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        current_step = (run_time // self.step_time) + 1
        user_count = current_step * self.step_load

        return (user_count, self.spawn_rate)


class WaveLoadShape(LoadTestShape):
    """
    Load pattern with waves

    Creates waves of traffic to simulate real-world patterns
    """

    time_limit = 300
    spawn_rate = 10

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        # Wave pattern using sine wave
        import math
        wave = (math.sin(run_time / 30) + 1) * 50  # Oscillate between 0-100 users
        user_count = int(wave)

        return (user_count, self.spawn_rate)


# Usage instructions in docstring at top of file
"""
Example Load Test Scenarios:

1. Baseline Test (10 users, 2 minutes):
   locust -f locustfile.py --host=http://localhost:8009 --users 10 --spawn-rate 2 --run-time 2m --headless

2. Load Test (100 users, 5 minutes):
   locust -f locustfile.py --host=http://localhost:8009 --users 100 --spawn-rate 10 --run-time 5m --headless --html=load-test.html

3. Stress Test (200 users, 3 minutes):
   locust -f locustfile.py --host=http://localhost:8009 --users 200 --spawn-rate 20 --run-time 3m --headless

4. Spike Test (sudden jump to 150 users):
   locust -f locustfile.py --host=http://localhost:8009 --users 150 --spawn-rate 50 --run-time 2m --headless

5. Step Load (gradual ramp):
   locust -f locustfile.py --host=http://localhost:8009 --headless --html=step-load.html

6. Realistic User Behavior:
   locust -f locustfile.py --host=http://localhost:8009 --users 50 --spawn-rate 5 --run-time 10m --headless

7. Web UI (interactive):
   locust -f locustfile.py --host=http://localhost:8009
   # Then open http://localhost:8089
"""
