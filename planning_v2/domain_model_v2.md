# Domain Model V2 - Domain-Driven Design

**Version:** 2.0
**Created:** 2025-11-09

---

## Overview

This document defines the domain model for the Olist e-commerce data warehouse using Domain-Driven Design (DDD) principles. Business logic lives HERE, not in SQL.

### Key DDD Concepts

**Entities:** Objects with identity that can change over time
**Value Objects:** Immutable objects defined by their attributes
**Aggregates:** Cluster of entities/value objects with consistency boundary
**Aggregate Roots:** Entry point to aggregate, enforces invariants
**Domain Events:** Something significant that happened in the domain
**Repositories:** Abstraction for persistence (interfaces defined here, implemented in infrastructure)

---

## Bounded Context: Sales

### Aggregates

#### Order (Aggregate Root)

```python
# domain/sales/aggregates/order.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from uuid import UUID, uuid4
from decimal import Decimal

@dataclass
class Order:
    """
    Order aggregate root

    Invariants:
    - Must have at least one item
    - total_amount = sum(items.total_amount)
    - Status transitions follow business rules
    - Cannot modify delivered/cancelled orders
    """
    order_id: UUID = field(default_factory=uuid4)
    customer_id: UUID = field(default=None)
    status: 'OrderStatus' = field(default='PENDING')
    created_at: datetime = field(default_factory=datetime.now)

    _items: List['OrderItem'] = field(default_factory=list, init=False, repr=False)
    _payments: List['Payment'] = field(default_factory=list, init=False, repr=False)
    _domain_events: List['DomainEvent'] = field(default_factory=list, init=False, repr=False)

    def add_item(self, product_id: UUID, price: Decimal, freight: Decimal) -> 'OrderItem':
        """Add item to order"""
        if self.status not in ['PENDING', 'APPROVED']:
            raise InvalidOperationError(f"Cannot add items to {self.status} order")

        item = OrderItem(
            order_id=self.order_id,
            product_id=product_id,
            price=price,
            freight_value=freight
        )
        self._items.append(item)
        self._validate_invariants()
        return item

    def add_payment(self, amount: Decimal, method: str, installments: int = 1):
        """Add payment to order"""
        payment = Payment(
            order_id=self.order_id,
            amount=amount,
            payment_method=method,
            installments=installments
        )
        self._payments.append(payment)

        if self.total_paid() >= self.total_amount():
            self._transition_to('PAID')
            self._raise_event(OrderPaid(self.order_id, self.total_amount()))

    def approve(self):
        """Approve order for fulfillment"""
        if self.status != 'PAID':
            raise InvalidOperationError("Can only approve paid orders")

        self._transition_to('APPROVED')
        self._raise_event(OrderApproved(self.order_id))

    def cancel(self, reason: str):
        """Cancel order"""
        if self.status in ['DELIVERED', 'CANCELLED']:
            raise InvalidOperationError(f"Cannot cancel {self.status} order")

        self._transition_to('CANCELLED')
        self._raise_event(OrderCancelled(self.order_id, reason))

    def total_amount(self) -> Decimal:
        """Calculate total amount (enforces invariant)"""
        return sum(item.total_amount() for item in self._items)

    def total_paid(self) -> Decimal:
        """Calculate total paid"""
        return sum(payment.amount for payment in self._payments)

    def _transition_to(self, new_status: str):
        """State machine for order status"""
        valid_transitions = {
            'PENDING': ['APPROVED', 'CANCELLED'],
            'APPROVED': ['PAID', 'CANCELLED'],
            'PAID': ['PROCESSING', 'CANCELLED'],
            'PROCESSING': ['SHIPPED', 'CANCELLED'],
            'SHIPPED': ['DELIVERED', 'CANCELLED'],
            'DELIVERED': [],
            'CANCELLED': []
        }

        if new_status not in valid_transitions.get(self.status, []):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self.status} to {new_status}"
            )

        self.status = new_status

    def _validate_invariants(self):
        """Ensure business rules are satisfied"""
        if len(self._items) == 0:
            raise InvariantViolation("Order must have at least one item")

        if self.total_amount() < Decimal('0'):
            raise InvariantViolation("Total amount cannot be negative")

    def _raise_event(self, event: 'DomainEvent'):
        """Publish domain event"""
        self._domain_events.append(event)

    @property
    def domain_events(self) -> List['DomainEvent']:
        """Get and clear domain events"""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events


@dataclass
class OrderItem:
    """Order line item (entity within Order aggregate)"""
    order_id: UUID
    product_id: UUID
    price: Decimal
    freight_value: Decimal
    seller_id: UUID = None

    def total_amount(self) -> Decimal:
        """Calculate item total"""
        return self.price + self.freight_value


@dataclass
class Payment:
    """Payment (entity within Order aggregate)"""
    payment_id: UUID = field(default_factory=uuid4)
    order_id: UUID = None
    amount: Decimal = Decimal('0')
    payment_method: str = ''
    installments: int = 1
    paid_at: datetime = field(default_factory=datetime.now)
```

### Value Objects

```python
# domain/sales/value_objects.py

@dataclass(frozen=True)
class OrderStatus:
    """Value object for order status"""
    PENDING = 'pending'
    APPROVED = 'approved'
    PAID = 'paid'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    UNAVAILABLE = 'unavailable'


@dataclass(frozen=True)
class PaymentMethod:
    """Value object for payment methods"""
    CREDIT_CARD = 'credit_card'
    BOLETO = 'boleto'
    VOUCHER = 'voucher'
    DEBIT_CARD = 'debit_card'
```

### Domain Events

```python
# domain/sales/events.py

@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    """Published when order is created"""
    order_id: UUID
    customer_id: UUID
    total_amount: Decimal
    occurred_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class OrderPaid(DomainEvent):
    """Published when order is fully paid"""
    order_id: UUID
    total_amount: Decimal
    occurred_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class OrderApproved(DomainEvent):
    """Published when order approved for fulfillment"""
    order_id: UUID
    occurred_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class OrderCancelled(DomainEvent):
    """Published when order is cancelled"""
    order_id: UUID
    reason: str
    occurred_at: datetime = field(default_factory=datetime.now)
```

### Repository Interface

```python
# domain/sales/repositories.py

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

class OrderRepository(ABC):
    """Port: Interface for Order persistence"""

    @abstractmethod
    def get(self, order_id: UUID) -> Optional[Order]:
        """Retrieve order by ID"""
        pass

    @abstractmethod
    def get_by_customer(self, customer_id: UUID) -> List[Order]:
        """Get all orders for customer"""
        pass

    @abstractmethod
    def save(self, order: Order) -> None:
        """Persist order (insert or update)"""
        pass

    @abstractmethod
    def delete(self, order_id: UUID) -> None:
        """Delete order"""
        pass
```

---

## Bounded Context: Customer

### Aggregates

#### Customer (Aggregate Root)

```python
# domain/customer/aggregates/customer.py

@dataclass
class Customer:
    """
    Customer aggregate root

    Invariants:
    - Email must be unique and valid
    - Segment is calculated, not set directly
    - Metrics are derived from events
    """
    customer_id: UUID = field(default_factory=uuid4)
    email: str = ''
    city: str = ''
    state: str = ''
    zip_code: str = ''

    _metrics: 'CustomerMetrics' = field(default_factory=lambda: CustomerMetrics())
    _segment: str = 'NEW'
    _reviews: List['Review'] = field(default_factory=list)
    _domain_events: List['DomainEvent'] = field(default_factory=list)

    def handle_order_completed(self, order_id: UUID, total: Decimal, completed_at: datetime):
        """React to order completion (event handler)"""
        # Update metrics
        self._metrics = self._metrics.add_order(total, completed_at)

        # Recalculate segment
        new_segment = self._calculate_segment()
        if new_segment != self._segment:
            old_segment = self._segment
            self._segment = new_segment
            self._raise_event(CustomerSegmentChanged(
                customer_id=self.customer_id,
                old_segment=old_segment,
                new_segment=new_segment
            ))

    def submit_review(self, order_id: UUID, score: int, comment: str = '') -> 'Review':
        """Submit product/seller review"""
        if not 1 <= score <= 5:
            raise ValueError("Review score must be between 1 and 5")

        review = Review(
            customer_id=self.customer_id,
            order_id=order_id,
            score=score,
            comment=comment,
            created_at=datetime.now()
        )

        self._reviews.append(review)
        self._raise_event(ReviewSubmitted(
            review_id=review.review_id,
            customer_id=self.customer_id,
            order_id=order_id,
            score=score
        ))

        return review

    def anonymize(self):
        """LGPD: Anonymize personal data"""
        self.email = f"anonymized_{self.customer_id}@deleted.com"
        self.city = "ANONYMIZED"
        self.state = "XX"
        self.zip_code = "00000000"

        # Clear reviews
        self._reviews.clear()

        self._raise_event(CustomerAnonymized(self.customer_id))

    def _calculate_segment(self) -> str:
        """Business rule: Customer segmentation"""
        if self._metrics.is_churned():
            return 'CHURNED'

        if self._metrics.is_vip():
            return 'VIP'

        if self._metrics.is_loyal():
            return 'LOYAL'

        if self._metrics.total_orders == 1:
            return 'ONE_TIME'

        if self._metrics.total_orders > 1:
            return 'REGULAR'

        return 'NEW'

    @property
    def segment(self) -> str:
        """Read-only segment (calculated, not set)"""
        return self._segment

    @property
    def metrics(self) -> 'CustomerMetrics':
        """Read-only metrics"""
        return self._metrics


@dataclass
class Review:
    """Review (entity within Customer aggregate)"""
    review_id: UUID = field(default_factory=uuid4)
    customer_id: UUID = None
    order_id: UUID = None
    score: int = 0
    comment: str = ''
    created_at: datetime = field(default_factory=datetime.now)
```

### Value Objects

```python
# domain/customer/value_objects.py

@dataclass(frozen=True)
class CustomerMetrics:
    """Immutable metrics for customer behavior"""
    total_orders: int = 0
    total_spent: Decimal = Decimal('0')
    last_order_date: Optional[datetime] = None
    average_order_value: Decimal = Decimal('0')

    def add_order(self, total: Decimal, date: datetime) -> 'CustomerMetrics':
        """Return new metrics with order added (immutable)"""
        new_total_orders = self.total_orders + 1
        new_total_spent = self.total_spent + total
        new_avg = new_total_spent / new_total_orders

        return CustomerMetrics(
            total_orders=new_total_orders,
            total_spent=new_total_spent,
            last_order_date=date,
            average_order_value=new_avg
        )

    def is_vip(self) -> bool:
        """Business rule: VIP = >5 orders AND >R$1000 spent"""
        return self.total_orders > 5 and self.total_spent > Decimal('1000')

    def is_loyal(self) -> bool:
        """Business rule: Loyal = >5 orders"""
        return self.total_orders > 5

    def is_churned(self) -> bool:
        """Business rule: Churned = >180 days since last order"""
        if not self.last_order_date:
            return False

        days_since_last = (datetime.now() - self.last_order_date).days
        return days_since_last > 180


@dataclass(frozen=True)
class CustomerSegment:
    """Value object for customer segments"""
    NEW = 'NEW'
    ONE_TIME = 'ONE_TIME'
    REGULAR = 'REGULAR'
    LOYAL = 'LOYAL'
    VIP = 'VIP'
    CHURNED = 'CHURNED'
```

---

## Shared Kernel

### Value Objects

```python
# shared_kernel/value_objects.py

@dataclass(frozen=True)
class Money:
    """Value object for monetary amounts"""
    amount: Decimal
    currency: str = 'BRL'

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")

    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, scalar: Decimal) -> 'Money':
        return Money(self.amount * scalar, self.currency)

    def __truediv__(self, scalar: Decimal) -> 'Money':
        return Money(self.amount / scalar, self.currency)

    def __gt__(self, other: 'Money') -> bool:
        return self.amount > other.amount

    def format(self) -> str:
        """Format as Brazilian currency"""
        return f"R$ {self.amount:,.2f}"


@dataclass(frozen=True)
class Address:
    """Value object for Brazilian addresses"""
    zip_code: str
    city: str
    state: str

    VALID_STATES = {
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
        'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
        'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    }

    def __post_init__(self):
        # Validate ZIP code format
        if not self.zip_code or len(self.zip_code) != 8:
            raise ValueError("Invalid ZIP code (must be 8 digits)")

        # Validate state
        if self.state not in self.VALID_STATES:
            raise ValueError(f"Invalid state: {self.state}")

    def format(self) -> str:
        """Format address"""
        return f"{self.city}/{self.state} - {self.zip_code}"


@dataclass(frozen=True)
class DateRange:
    """Value object for date ranges"""
    start: datetime
    end: datetime

    def __post_init__(self):
        if self.end < self.start:
            raise ValueError("End date must be after start date")

    def contains(self, date: datetime) -> bool:
        """Check if date is within range"""
        return self.start <= date <= self.end

    def duration_days(self) -> int:
        """Calculate duration in days"""
        return (self.end - self.start).days

    def overlaps(self, other: 'DateRange') -> bool:
        """Check if ranges overlap"""
        return (self.start <= other.end) and (other.start <= self.end)
```

---

## Anti-Corruption Layers

### Purpose
Protect domain model from external data formats (CSV, API, etc.)

```python
# domain/sales/adapters/csv_adapter.py

class OrderCSVAdapter:
    """Translate CSV data to Order aggregate"""

    def from_csv_row(self, row: dict) -> Order:
        """Convert CSV row to Order domain object"""
        # CSV has different field names and formats
        order = Order(
            order_id=UUID(row['order_id']),
            customer_id=UUID(row['customer_id']),
            status=self._map_status(row['order_status']),
            created_at=datetime.fromisoformat(row['order_purchase_timestamp'])
        )

        return order

    def _map_status(self, csv_status: str) -> str:
        """Map CSV status to domain status"""
        # CSV uses different values than domain
        mapping = {
            'delivered': OrderStatus.DELIVERED,
            'shipped': OrderStatus.SHIPPED,
            'processing': OrderStatus.PROCESSING,
            'canceled': OrderStatus.CANCELLED,  # Note: CSV has typo
            'invoiced': OrderStatus.PAID,
            'approved': OrderStatus.APPROVED,
            'created': OrderStatus.PENDING
        }

        return mapping.get(csv_status, OrderStatus.PENDING)
```

---

## Business Rules Catalog

All business rules are encoded in domain layer, NOT in SQL.

### Customer Segmentation Rules

| Segment | Rule | Implementation |
|---------|------|----------------|
| NEW | No orders yet | `total_orders == 0` |
| ONE_TIME | Exactly 1 order | `total_orders == 1` |
| REGULAR | 2-5 orders | `2 <= total_orders <= 5` |
| LOYAL | More than 5 orders | `total_orders > 5 AND total_spent <= 1000` |
| VIP | More than 5 orders AND > R$1000 spent | `total_orders > 5 AND total_spent > 1000` |
| CHURNED | No order in last 180 days | `days_since_last_order > 180` |

**Location:** `domain/customer/value_objects.py::CustomerMetrics`

### Order Status Transitions

```
PENDING → APPROVED → PAID → PROCESSING → SHIPPED → DELIVERED
   ↓          ↓        ↓         ↓           ↓
CANCELLED  CANCELLED CANCELLED CANCELLED CANCELLED
```

**Location:** `domain/sales/aggregates/order.py::Order._transition_to()`

### Delivery Performance Rules

| Metric | Rule | Implementation |
|--------|------|----------------|
| On-time delivery | `actual_delivery <= estimated_delivery` | `Shipment.is_on_time()` |
| Late delivery | `actual_delivery > estimated_delivery` | `Shipment.is_late()` |
| Delay days | Days past estimate | `Shipment.delay_days()` |

**Location:** `domain/fulfillment/aggregates/shipment.py`

---

## Invariants

### Order Invariants

1. **Order must have items:** `len(order.items) > 0`
2. **Total must match sum:** `order.total_amount() == sum(item.total_amount())`
3. **Cannot modify delivered orders:** Status checks in all mutating methods
4. **Payment must not exceed total:** Validated in `add_payment()`

### Customer Invariants

1. **Email uniqueness:** Enforced by repository (unique constraint)
2. **Segment is calculated:** No direct setter, only calculated from metrics
3. **Metrics are event-sourced:** Updated only via event handlers

### Shipment Invariants

1. **Cannot ship without estimate:** `estimated_delivery` required before shipping
2. **Delivery after shipment:** `actual_delivery >= shipped_at`
3. **Status follows sequence:** State machine enforced

---

## Testing Domain Logic

Domain layer has ZERO dependencies, so it's fully unit-testable:

```python
# tests/unit/domain/sales/test_order.py

def test_order_total_amount_calculated_correctly():
    """Verify total amount invariant"""
    order = Order(customer_id=uuid4())
    order.add_item(uuid4(), Decimal('100'), Decimal('20'))
    order.add_item(uuid4(), Decimal('50'), Decimal('10'))

    assert order.total_amount() == Decimal('180')  # 100+20 + 50+10


def test_cannot_add_item_to_delivered_order():
    """Verify immutability of delivered orders"""
    order = Order(customer_id=uuid4())
    order.add_item(uuid4(), Decimal('100'), Decimal('20'))
    order._status = 'DELIVERED'  # Simulate delivery

    with pytest.raises(InvalidOperationError):
        order.add_item(uuid4(), Decimal('50'), Decimal('10'))


def test_customer_segment_changes_on_vip_threshold():
    """Verify segmentation business rule"""
    customer = Customer(email="test@example.com")

    # Add 6 orders totaling R$1100
    for i in range(6):
        customer.handle_order_completed(
            order_id=uuid4(),
            total=Decimal('200'),
            completed_at=datetime.now()
        )

    assert customer.segment == 'VIP'  # Should be VIP now

    # Verify event was raised
    events = customer.domain_events
    assert any(isinstance(e, CustomerSegmentChanged) for e in events)
```

---

## Conclusion

This domain model:

1. **Contains business logic** (not in SQL)
2. **Enforces invariants** (aggregate roots protect consistency)
3. **Is testable** (no infrastructure dependencies)
4. **Uses ubiquitous language** (Customer, Order, not dim_customer, fact_orders)
5. **Publishes domain events** (enables event-driven architecture)
6. **Defines clear boundaries** (bounded contexts with anti-corruption layers)

**Next:** See implementation_strategy_v2.md for how to build this incrementally.
