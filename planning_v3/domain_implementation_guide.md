# Domain Model Implementation Guide V3

**Document Version:** 3.0
**Date:** 2025-11-09
**Purpose:** Complete implementation guide for the domain layer following DDD principles
**Status:** Implementation Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Domain Model Structure](#domain-model-structure)
3. [Value Objects](#value-objects)
4. [Entities](#entities)
5. [Aggregates](#aggregates)
6. [Domain Events](#domain-events)
7. [Repositories](#repositories)
8. [Domain Services](#domain-services)
9. [Implementation Checklist](#implementation-checklist)

---

## Overview

### What is Domain-Driven Design?

**Domain-Driven Design (DDD)** is an approach to software development that puts the business domain at the center of the design. Key concepts:

**Value Objects:** Immutable objects defined by their attributes (Money, Address, DateRange)
**Entities:** Objects with identity that persist over time (Customer, Order, Product)
**Aggregates:** Clusters of entities with a root entity that enforces invariants
**Domain Events:** Things that happened in the domain (OrderPlaced, PaymentReceived)
**Repositories:** Persistence abstraction for aggregates
**Domain Services:** Business logic that doesn't belong to any entity

### Bounded Contexts for Olist

We have **4 bounded contexts** mapped to databases:

```
┌────────────────────────────────────────┐
│  SALES ANALYTICS CONTEXT (DuckDB)     │
│  • Order aggregate                     │
│  • OrderItem entity                    │
│  • Payment entity                      │
│  • Revenue calculations                │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│  CUSTOMER ANALYTICS CONTEXT (DuckDB)   │
│  • Customer aggregate                  │
│  • CustomerSegment entity              │
│  • Cohort analysis                     │
│  • RFM segmentation                    │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│  MARKETPLACE CONTEXT (DuckDB)          │
│  • Seller aggregate                    │
│  • Product aggregate                   │
│  • Category entity                     │
│  • Review entity                       │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│  FULFILLMENT CONTEXT (DuckDB)          │
│  • Delivery aggregate                  │
│  • ShippingPerformance value object    │
│  • Geography entity                    │
└────────────────────────────────────────┘
```

---

## Domain Model Structure

### Directory Layout

```
src/domain/
├── __init__.py
├── value_objects/
│   ├── __init__.py
│   ├── money.py              # Money (amount + currency)
│   ├── address.py            # Brazilian address
│   ├── date_range.py         # Date range with validation
│   ├── product_dimensions.py # Product physical dimensions
│   ├── geo_coordinates.py    # Latitude/longitude
│   └── review_score.py       # Review score (1-5)
│
├── entities/
│   ├── __init__.py
│   ├── order_item.py         # Order line item
│   ├── payment.py            # Payment transaction
│   ├── review.py             # Customer review
│   ├── category.py           # Product category
│   └── geography.py          # Geographic location
│
├── aggregates/
│   ├── __init__.py
│   ├── order.py              # Order aggregate root
│   ├── customer.py           # Customer aggregate root
│   ├── seller.py             # Seller aggregate root
│   ├── product.py            # Product aggregate root
│   └── delivery.py           # Delivery aggregate root
│
├── events/
│   ├── __init__.py
│   ├── base.py               # Base domain event
│   ├── order_events.py       # OrderPlaced, OrderCancelled
│   ├── customer_events.py    # CustomerRegistered
│   ├── payment_events.py     # PaymentReceived
│   └── delivery_events.py    # DeliveryCompleted
│
├── repositories/
│   ├── __init__.py
│   ├── base.py               # Base repository interface
│   ├── order_repository.py
│   ├── customer_repository.py
│   ├── seller_repository.py
│   └── product_repository.py
│
└── services/
    ├── __init__.py
    ├── segmentation_service.py    # Customer segmentation (RFM)
    ├── pricing_service.py         # Price calculations
    └── shipping_service.py        # Shipping cost calculations
```

---

## Value Objects

### 1. Money Value Object

**Location:** `src/domain/value_objects/money.py`

**Purpose:** Handle monetary values with currency

**Key Features:**
- Immutable (frozen dataclass)
- Currency validation
- Arithmetic operations (+, -, *)
- Comparison operations

**Implementation:**

```python
from decimal import Decimal
from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Money:
    """Immutable money value object"""

    amount: Decimal
    currency: str = 'BRL'

    def __post_init__(self):
        """Validate money"""
        # Convert to Decimal if needed
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))

        # Validate amount
        if self.amount < 0:
            raise ValueError(f"Money amount cannot be negative: {self.amount}")

        # Validate currency
        if self.currency not in ['BRL', 'USD', 'EUR']:
            raise ValueError(f"Unsupported currency: {self.currency}")

    def __add__(self, other: 'Money') -> 'Money':
        """Add money (same currency only)"""
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add different currencies: {self.currency} + {other.currency}"
            )
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        """Subtract money (same currency only)"""
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot subtract different currencies: {self.currency} - {other.currency}"
            )
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, multiplier: Union[int, float, Decimal]) -> 'Money':
        """Multiply money by scalar"""
        return Money(self.amount * Decimal(str(multiplier)), self.currency)

    def __eq__(self, other: object) -> bool:
        """Check equality"""
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: 'Money') -> bool:
        """Less than comparison (same currency only)"""
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount < other.amount

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"

    def __repr__(self) -> str:
        return f"Money({self.amount}, '{self.currency}')"

    @classmethod
    def zero(cls, currency: str = 'BRL') -> 'Money':
        """Create zero money"""
        return cls(Decimal('0.00'), currency)

    @classmethod
    def from_float(cls, amount: float, currency: str = 'BRL') -> 'Money':
        """Create money from float"""
        return cls(Decimal(str(amount)), currency)
```

**Usage:**
```python
# Create money
price = Money(Decimal('100.50'), 'BRL')
freight = Money.from_float(15.75, 'BRL')

# Arithmetic
total = price + freight  # Money(116.25, 'BRL')
discount = price * 0.10  # Money(10.05, 'BRL')

# Comparison
if price > Money.zero('BRL'):
    print("Price is positive")
```

### 2. Address Value Object

**Location:** `src/domain/value_objects/address.py`

**Purpose:** Brazilian address with validation

```python
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Address:
    """Brazilian address value object"""

    zip_code: str  # CEP (8 digits: 12345-678)
    city: str
    state: str  # 2-letter state code (SP, RJ, MG, etc.)
    street: Optional[str] = None
    number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None

    # Brazilian states
    VALID_STATES = {
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
        'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
        'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    }

    # Brazilian regions
    STATE_TO_REGION = {
        'AC': 'Norte', 'AM': 'Norte', 'AP': 'Norte', 'PA': 'Norte',
        'RO': 'Norte', 'RR': 'Norte', 'TO': 'Norte',
        'AL': 'Nordeste', 'BA': 'Nordeste', 'CE': 'Nordeste',
        'MA': 'Nordeste', 'PB': 'Nordeste', 'PE': 'Nordeste',
        'PI': 'Nordeste', 'RN': 'Nordeste', 'SE': 'Nordeste',
        'DF': 'Centro-Oeste', 'GO': 'Centro-Oeste', 'MT': 'Centro-Oeste',
        'MS': 'Centro-Oeste',
        'ES': 'Sudeste', 'MG': 'Sudeste', 'RJ': 'Sudeste', 'SP': 'Sudeste',
        'PR': 'Sul', 'RS': 'Sul', 'SC': 'Sul'
    }

    def __post_init__(self):
        """Validate address"""
        # Validate state
        if self.state not in self.VALID_STATES:
            raise ValueError(f"Invalid Brazilian state: {self.state}")

        # Validate zip code format (12345678 or 12345-678)
        zip_clean = self.zip_code.replace('-', '')
        if not zip_clean.isdigit() or len(zip_clean) != 8:
            raise ValueError(f"Invalid Brazilian ZIP code: {self.zip_code}")

    @property
    def region(self) -> str:
        """Get Brazilian region for this state"""
        return self.STATE_TO_REGION[self.state]

    @property
    def formatted_zip_code(self) -> str:
        """Get formatted ZIP code (12345-678)"""
        zip_clean = self.zip_code.replace('-', '')
        return f"{zip_clean[:5]}-{zip_clean[5:]}"

    def __str__(self) -> str:
        return f"{self.city}, {self.state} {self.formatted_zip_code}"
```

### 3. Review Score Value Object

**Location:** `src/domain/value_objects/review_score.py`

```python
from dataclasses import dataclass
from enum import Enum


class ReviewRating(Enum):
    """Review rating enumeration"""
    VERY_BAD = 1
    BAD = 2
    NEUTRAL = 3
    GOOD = 4
    EXCELLENT = 5


@dataclass(frozen=True)
class ReviewScore:
    """Review score value object (1-5 stars)"""

    score: int

    def __post_init__(self):
        """Validate review score"""
        if not 1 <= self.score <= 5:
            raise ValueError(f"Review score must be between 1 and 5, got: {self.score}")

    @property
    def rating(self) -> ReviewRating:
        """Get rating enum"""
        return ReviewRating(self.score)

    @property
    def is_positive(self) -> bool:
        """Check if review is positive (4-5 stars)"""
        return self.score >= 4

    @property
    def is_negative(self) -> bool:
        """Check if review is negative (1-2 stars)"""
        return self.score <= 2

    def __str__(self) -> str:
        return f"{self.score} stars ({self.rating.name})"
```

---

## Entities

### 1. OrderItem Entity

**Location:** `src/domain/entities/order_item.py`

**Purpose:** Line item within an order

```python
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from ..value_objects.money import Money


@dataclass
class OrderItem:
    """Order line item entity"""

    order_item_id: str
    order_id: str
    product_id: str
    seller_id: str
    price: Money
    freight_value: Money
    shipping_limit_date: datetime

    def __post_init__(self):
        """Validate order item"""
        if not self.order_item_id:
            raise ValueError("Order item ID cannot be empty")

        if self.price.amount < 0:
            raise ValueError("Price cannot be negative")

        if self.freight_value.amount < 0:
            raise ValueError("Freight value cannot be negative")

    @property
    def total_amount(self) -> Money:
        """Calculate total (price + freight)"""
        return self.price + self.freight_value

    @property
    def has_freight(self) -> bool:
        """Check if item has freight cost"""
        return self.freight_value.amount > 0

    def __eq__(self, other: object) -> bool:
        """Check equality based on order_item_id"""
        if not isinstance(other, OrderItem):
            return False
        return self.order_item_id == other.order_item_id

    def __hash__(self) -> int:
        return hash(self.order_item_id)
```

### 2. Payment Entity

**Location:** `src/domain/entities/payment.py`

```python
from dataclasses import dataclass
from enum import Enum
from ..value_objects.money import Money


class PaymentType(Enum):
    """Payment type enumeration"""
    CREDIT_CARD = "credit_card"
    BOLETO = "boleto"
    VOUCHER = "voucher"
    DEBIT_CARD = "debit_card"


@dataclass
class Payment:
    """Payment entity"""

    payment_id: str
    order_id: str
    payment_type: PaymentType
    installments: int
    value: Money

    def __post_init__(self):
        """Validate payment"""
        if self.installments < 1:
            raise ValueError("Installments must be at least 1")

        if self.installments > 24:
            raise ValueError("Maximum 24 installments allowed")

        if self.value.amount <= 0:
            raise ValueError("Payment value must be positive")

        # Boleto and voucher don't allow installments
        if self.payment_type in [PaymentType.BOLETO, PaymentType.VOUCHER]:
            if self.installments > 1:
                raise ValueError(
                    f"{self.payment_type.value} does not allow installments"
                )

    @property
    def installment_value(self) -> Money:
        """Calculate value per installment"""
        from decimal import Decimal
        amount = self.value.amount / Decimal(self.installments)
        return Money(amount, self.value.currency)

    @property
    def is_installment_payment(self) -> bool:
        """Check if payment is installment"""
        return self.installments > 1
```

---

## Aggregates

### 1. Order Aggregate Root

**Location:** `src/domain/aggregates/order.py`

**Purpose:** Order aggregate that enforces business rules

```python
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum

from ..entities.order_item import OrderItem
from ..entities.payment import Payment
from ..value_objects.money import Money
from ..events.order_events import OrderPlaced, OrderApproved, OrderCancelled


class OrderStatus(Enum):
    """Order status enumeration"""
    CREATED = "created"
    APPROVED = "approved"
    INVOICED = "invoiced"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


@dataclass
class Order:
    """Order aggregate root

    Enforces business invariants:
    - Order must have at least one item
    - Total payment must equal total items amount
    - Cannot modify delivered/cancelled orders
    """

    order_id: str
    customer_id: str
    status: OrderStatus
    order_date: datetime
    items: List[OrderItem] = field(default_factory=list)
    payments: List[Payment] = field(default_factory=list)
    approved_at: Optional[datetime] = None
    delivered_carrier_date: Optional[datetime] = None
    delivered_customer_date: Optional[datetime] = None
    estimated_delivery_date: Optional[datetime] = None

    # Domain events (not persisted)
    _events: List = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        """Validate order after initialization"""
        if not self.order_id:
            raise ValueError("Order ID cannot be empty")

        if not self.customer_id:
            raise ValueError("Customer ID cannot be empty")

        # Must have at least one item
        if not self.items:
            raise ValueError("Order must have at least one item")

    # === Properties ===

    @property
    def total_items_amount(self) -> Money:
        """Calculate total amount from items (price + freight)"""
        total = Money.zero('BRL')
        for item in self.items:
            total = total + item.total_amount
        return total

    @property
    def total_payments_amount(self) -> Money:
        """Calculate total from payments"""
        total = Money.zero('BRL')
        for payment in self.payments:
            total = total + payment.value
        return total

    @property
    def total_items(self) -> int:
        """Count total items"""
        return len(self.items)

    @property
    def total_sellers(self) -> int:
        """Count unique sellers"""
        return len(set(item.seller_id for item in self.items))

    @property
    def is_multivendor(self) -> bool:
        """Check if order has multiple sellers"""
        return self.total_sellers > 1

    @property
    def is_delivered(self) -> bool:
        """Check if order is delivered"""
        return self.status == OrderStatus.DELIVERED

    @property
    def is_cancelled(self) -> bool:
        """Check if order is cancelled"""
        return self.status == OrderStatus.CANCELLED

    @property
    def can_be_modified(self) -> bool:
        """Check if order can be modified"""
        return self.status not in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]

    @property
    def delivery_time_days(self) -> Optional[int]:
        """Calculate delivery time in days"""
        if not (self.order_date and self.delivered_customer_date):
            return None
        return (self.delivered_customer_date - self.order_date).days

    @property
    def is_late_delivery(self) -> Optional[bool]:
        """Check if delivery was late"""
        if not (self.delivered_customer_date and self.estimated_delivery_date):
            return None
        return self.delivered_customer_date > self.estimated_delivery_date

    # === Business Methods ===

    def add_item(self, item: OrderItem) -> None:
        """Add item to order

        Business Rules:
        - Cannot add items to delivered/cancelled orders
        - Item must belong to this order
        """
        if not self.can_be_modified:
            raise ValueError(
                f"Cannot add items to {self.status.value} order"
            )

        if item.order_id != self.order_id:
            raise ValueError(
                f"Item belongs to different order: {item.order_id}"
            )

        # Check for duplicates
        if item in self.items:
            raise ValueError(
                f"Item {item.order_item_id} already exists in order"
            )

        self.items.append(item)

    def add_payment(self, payment: Payment) -> None:
        """Add payment to order

        Business Rules:
        - Cannot add payments to delivered/cancelled orders
        - Payment must belong to this order
        - Total payments cannot exceed total items amount
        """
        if not self.can_be_modified:
            raise ValueError(
                f"Cannot add payments to {self.status.value} order"
            )

        if payment.order_id != self.order_id:
            raise ValueError(
                f"Payment belongs to different order: {payment.order_id}"
            )

        # Check if adding this payment would exceed total
        new_total = self.total_payments_amount + payment.value
        if new_total > self.total_items_amount:
            raise ValueError(
                f"Total payments ({new_total}) would exceed "
                f"total items amount ({self.total_items_amount})"
            )

        self.payments.append(payment)

    def approve(self) -> None:
        """Approve the order

        Business Rules:
        - Can only approve created orders
        - Must have at least one payment
        - Total payments must equal total items amount
        """
        if self.status != OrderStatus.CREATED:
            raise ValueError(
                f"Can only approve created orders, current status: {self.status.value}"
            )

        if not self.payments:
            raise ValueError("Cannot approve order without payment")

        if self.total_payments_amount != self.total_items_amount:
            raise ValueError(
                f"Payment mismatch: paid {self.total_payments_amount}, "
                f"total {self.total_items_amount}"
            )

        self.status = OrderStatus.APPROVED
        self.approved_at = datetime.now()

        # Emit domain event
        self._events.append(OrderApproved(self.order_id, self.approved_at))

    def cancel(self, reason: str) -> None:
        """Cancel the order

        Business Rules:
        - Cannot cancel delivered orders
        - Cannot cancel already cancelled orders
        """
        if self.status == OrderStatus.DELIVERED:
            raise ValueError("Cannot cancel delivered order")

        if self.status == OrderStatus.CANCELLED:
            raise ValueError("Order is already cancelled")

        self.status = OrderStatus.CANCELLED

        # Emit domain event
        self._events.append(OrderCancelled(self.order_id, reason, datetime.now()))

    def mark_as_delivered(self, delivered_date: datetime) -> None:
        """Mark order as delivered

        Business Rules:
        - Can only deliver shipped orders
        - Delivery date must be after order date
        """
        if self.status != OrderStatus.SHIPPED:
            raise ValueError(
                f"Can only deliver shipped orders, current status: {self.status.value}"
            )

        if delivered_date < self.order_date:
            raise ValueError("Delivery date cannot be before order date")

        self.status = OrderStatus.DELIVERED
        self.delivered_customer_date = delivered_date

    def get_events(self) -> List:
        """Get and clear domain events"""
        events = self._events.copy()
        self._events.clear()
        return events

    def __eq__(self, other: object) -> bool:
        """Check equality based on order_id"""
        if not isinstance(other, Order):
            return False
        return self.order_id == other.order_id

    def __hash__(self) -> int:
        return hash(self.order_id)
```

---

## Domain Events

### Order Events

**Location:** `src/domain/events/order_events.py`

```python
from dataclasses import dataclass
from datetime import datetime
from .base import DomainEvent


@dataclass(frozen=True)
class OrderPlaced(DomainEvent):
    """Order was placed"""
    order_id: str
    order_date: datetime
    customer_id: str
    total_amount: str  # Decimal as string for serialization

    @property
    def event_type(self) -> str:
        return "order.placed"


@dataclass(frozen=True)
class OrderApproved(DomainEvent):
    """Order was approved"""
    order_id: str
    approved_at: datetime

    @property
    def event_type(self) -> str:
        return "order.approved"


@dataclass(frozen=True)
class OrderCancelled(DomainEvent):
    """Order was cancelled"""
    order_id: str
    reason: str
    cancelled_at: datetime

    @property
    def event_type(self) -> str:
        return "order.cancelled"


@dataclass(frozen=True)
class OrderDelivered(DomainEvent):
    """Order was delivered"""
    order_id: str
    delivered_at: datetime
    was_late: bool

    @property
    def event_type(self) -> str:
        return "order.delivered"
```

---

## Implementation Checklist

### Phase 1: Core Value Objects (Week 1)
- [ ] Money value object
- [ ] Address value object
- [ ] ReviewScore value object
- [ ] DateRange value object
- [ ] ProductDimensions value object
- [ ] Unit tests for all value objects

### Phase 2: Entities (Week 2)
- [ ] OrderItem entity
- [ ] Payment entity
- [ ] Review entity
- [ ] Category entity
- [ ] Geography entity
- [ ] Unit tests for all entities

### Phase 3: Aggregates (Week 3-4)
- [ ] Order aggregate root
- [ ] Customer aggregate root
- [ ] Seller aggregate root
- [ ] Product aggregate root
- [ ] Delivery aggregate root
- [ ] Unit tests for all aggregates

### Phase 4: Domain Events (Week 5)
- [ ] Base domain event
- [ ] Order events
- [ ] Customer events
- [ ] Payment events
- [ ] Delivery events
- [ ] Event dispatcher

### Phase 5: Repositories (Week 6)
- [ ] Base repository interface
- [ ] Order repository
- [ ] Customer repository
- [ ] Seller repository
- [ ] Product repository
- [ ] Integration tests

### Phase 6: Domain Services (Week 7)
- [ ] Customer segmentation service (RFM)
- [ ] Pricing service
- [ ] Shipping cost calculator
- [ ] Unit tests for services

---

## Next Steps

1. ✅ **Review this guide** - Understand DDD principles
2. ⏭️ **Implement value objects** - Start with Money, Address
3. ⏭️ **Implement entities** - OrderItem, Payment
4. ⏭️ **Implement aggregates** - Order aggregate root
5. ⏭️ **Write tests** - TDD approach
6. ⏭️ **Integrate with repositories** - Connect to databases

**Ready to build the domain model? Let's start with value objects!** 🚀
