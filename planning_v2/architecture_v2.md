# Olist Data Warehouse - Architecture V2
## Clean Architecture with Domain-Driven Design

**Document Version:** 2.0
**Created:** 2025-11-09
**Status:** Architecture Design Phase

---

## Table of Contents

1. [Architectural Vision](#architectural-vision)
2. [Bounded Contexts](#bounded-contexts)
3. [Clean Architecture Layers](#clean-architecture-layers)
4. [Technology Stack](#technology-stack)
5. [Security Architecture](#security-architecture)
6. [Data Architecture](#data-architecture)
7. [Deployment Model](#deployment-model)
8. [Schema Evolution Strategy](#schema-evolution-strategy)
9. [Disaster Recovery](#disaster-recovery)
10. [Cost Analysis](#cost-analysis)

---

## Architectural Vision

### Core Principles

This architecture is built on four foundational principles that address the critical flaws identified in V1:

**1. Domain-Driven Design (DDD)**
- Business logic lives in domain layer, NOT in SQL
- Bounded contexts with clear boundaries
- Ubiquitous language shared between technical and business teams
- Aggregates protect invariants

**2. Clean Architecture (Hexagonal Architecture)**
- Dependencies point inward (toward domain)
- Infrastructure is replaceable (ports & adapters)
- Framework-independent business logic
- Testable without external dependencies

**3. Security by Design**
- Not bolted on as afterthought
- Authentication, authorization, encryption from day 1
- LGPD compliance built-in
- Audit logging for all data access

**4. Data Quality as First-Class Citizen**
- Quality is a bounded context, not just testing
- Quality metrics tracked and reported
- Automated quality gates prevent bad data
- Quality ownership clear and enforced

### Architectural Patterns

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  (Marimo Dashboards, APIs, CLI Tools)                       │
└───────────────────────┬─────────────────────────────────────┘
                        │ Uses
┌───────────────────────▼─────────────────────────────────────┐
│                   APPLICATION LAYER                          │
│  (Use Cases, Application Services, DTOs)                    │
│  - LoadCustomerDimension                                    │
│  - CalculateMonthlyRevenue                                  │
│  - AssessDataQuality                                        │
└───────────────────────┬─────────────────────────────────────┘
                        │ Orchestrates
┌───────────────────────▼─────────────────────────────────────┐
│                     DOMAIN LAYER                             │
│  (Aggregates, Entities, Value Objects, Domain Events)       │
│  - Customer, Order, Product, Shipment                       │
│  - Money, Address, DateRange                                │
│  - Business Rules & Invariants                              │
└───────────────────────┬─────────────────────────────────────┘
                        │ Persisted by
┌───────────────────────▼─────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                        │
│  (Repositories, Adapters, External Services)                │
│  - PostgreSQL Repository                                    │
│  - CSV Data Source Adapter                                  │
│  - Dagster Orchestration Adapter                            │
└─────────────────────────────────────────────────────────────┘
```

**Key Insight:** Domain layer has zero dependencies on infrastructure. It defines interfaces (ports) that infrastructure implements (adapters).

---

## Bounded Contexts

The Olist e-commerce domain is decomposed into **4 bounded contexts** with explicit boundaries:

### Context Map

```
┌──────────────────┐         ┌──────────────────┐
│  Sales Context   │────────▶│ Fulfillment      │
│                  │ Events  │  Context         │
│ - Order          │         │ - Shipment       │
│ - Payment        │         │ - Delivery       │
│ - Invoice        │         │ - Carrier        │
└──────┬───────────┘         └────────┬─────────┘
       │                              │
       │ Events                       │ Events
       │                              │
       ▼                              ▼
┌──────────────────┐         ┌──────────────────┐
│ Customer Context │         │ Marketplace      │
│                  │◀────────│  Context         │
│ - Customer       │ Events  │ - Product        │
│ - Review         │         │ - Seller         │
│ - Loyalty        │         │ - Catalog        │
└──────────────────┘         └──────────────────┘
       ▲                              ▲
       │                              │
       └──────────┬───────────────────┘
                  │
         ┌────────▼────────┐
         │ Shared Kernel   │
         │                 │
         │ - Money         │
         │ - Address       │
         │ - Geolocation   │
         │ - DateRange     │
         └─────────────────┘
```

### Context Relationships

| Upstream Context | Downstream Context | Integration Pattern | Events Published |
|------------------|-------------------|-------------------|-----------------|
| Sales | Fulfillment | Event-driven | OrderPlaced, PaymentReceived |
| Sales | Customer | Event-driven | OrderCompleted, OrderCancelled |
| Fulfillment | Customer | Event-driven | DeliveryCompleted, DeliveryDelayed |
| Marketplace | Sales | Shared Kernel | ProductListed, SellerApproved |

**Anti-Corruption Layers (ACL):**
- Each context translates external events to internal domain model
- No direct database joins between contexts
- Contexts communicate via published events or shared kernel

---

### 1. Sales Context

**Responsibility:** Order lifecycle from placement to invoicing

**Bounded Context Definition:**
```
Sales Context owns:
- Order placement and management
- Payment processing and reconciliation
- Invoice generation
- Order status tracking

Sales Context does NOT own:
- Customer profiles (Customer Context)
- Product inventory (Marketplace Context)
- Delivery logistics (Fulfillment Context)
```

**Core Aggregates:**

```python
# domain/sales/aggregates/order.py
class Order:  # Aggregate Root
    """
    Invariants:
    - Order must have at least one item
    - Total amount = sum of item totals
    - Status transitions follow business rules
    - Cannot modify delivered order
    """

    def __init__(self, order_id: OrderId, customer_id: CustomerId):
        self.order_id = order_id
        self.customer_id = customer_id
        self._items: List[OrderItem] = []
        self._payments: List[Payment] = []
        self._status = OrderStatus.PENDING

    def add_item(self, product_id: ProductId, price: Money, freight: Money):
        """Add item and validate total"""
        if self._status != OrderStatus.PENDING:
            raise InvalidOperationError("Cannot modify non-pending order")

        item = OrderItem(product_id, price, freight)
        self._items.append(item)
        self._validate_invariants()

    def add_payment(self, amount: Money, method: PaymentMethod):
        """Add payment and check if fully paid"""
        payment = Payment(amount, method)
        self._payments.append(payment)

        if self.total_paid() >= self.total_amount():
            self._status = OrderStatus.PAID
            self._publish_event(OrderPaid(self.order_id))

    def total_amount(self) -> Money:
        """Calculate total (enforces invariant)"""
        return sum(item.total() for item in self._items)

    def _validate_invariants(self):
        """Ensure business rules are satisfied"""
        if len(self._items) == 0:
            raise InvariantViolation("Order must have at least one item")

        if self.total_amount() < Money(0):
            raise InvariantViolation("Total cannot be negative")
```

**Domain Events:**
- `OrderPlaced` → Fulfillment Context
- `PaymentReceived` → Customer Context (loyalty points)
- `OrderCancelled` → Fulfillment Context, Customer Context
- `OrderCompleted` → Customer Context (review request)

**Database Schema:**
```sql
-- core.orders (owned by Sales Context)
CREATE TABLE core.orders (
    order_id UUID PRIMARY KEY,
    customer_id UUID NOT NULL,  -- Reference, not FK to Customer Context
    status VARCHAR(20) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    version INT NOT NULL  -- Optimistic locking
);

-- core.order_items
CREATE TABLE core.order_items (
    order_item_id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES core.orders(order_id),
    product_id UUID NOT NULL,  -- Reference, not FK to Marketplace Context
    price DECIMAL(10,2) NOT NULL,
    freight_value DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    CONSTRAINT check_total CHECK (total_amount = price + freight_value)
);

-- core.payments
CREATE TABLE core.payments (
    payment_id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES core.orders(order_id),
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    installments INT NOT NULL DEFAULT 1,
    paid_at TIMESTAMP NOT NULL
);
```

---

### 2. Fulfillment Context

**Responsibility:** Order delivery and logistics management

**Bounded Context Definition:**
```
Fulfillment Context owns:
- Shipment tracking
- Delivery scheduling and execution
- Carrier performance
- Delivery SLA monitoring

Fulfillment Context does NOT own:
- Order creation (Sales Context)
- Customer satisfaction (Customer Context)
```

**Core Aggregates:**

```python
# domain/fulfillment/aggregates/shipment.py
class Shipment:  # Aggregate Root
    """
    Invariants:
    - Actual delivery date must be after estimated
    - Status transitions: pending → shipped → delivered
    - Cannot ship without estimated delivery date
    """

    def __init__(self, shipment_id: ShipmentId, order_id: OrderId):
        self.shipment_id = shipment_id
        self.order_id = order_id
        self._status = ShipmentStatus.PENDING
        self._estimated_delivery: Optional[datetime] = None

    def ship(self, carrier: Carrier, estimated_delivery: datetime):
        """Mark as shipped and set delivery estimate"""
        if self._status != ShipmentStatus.PENDING:
            raise InvalidOperationError("Already shipped")

        self._carrier = carrier
        self._estimated_delivery = estimated_delivery
        self._shipped_at = datetime.now()
        self._status = ShipmentStatus.SHIPPED

        self._publish_event(ShipmentDispatched(
            shipment_id=self.shipment_id,
            order_id=self.order_id,
            estimated_delivery=estimated_delivery
        ))

    def deliver(self, actual_delivery: datetime):
        """Mark as delivered and calculate delay"""
        if self._status != ShipmentStatus.SHIPPED:
            raise InvalidOperationError("Not shipped yet")

        self._actual_delivery = actual_delivery
        self._status = ShipmentStatus.DELIVERED

        delay = self._calculate_delay()

        if delay > timedelta(days=0):
            self._publish_event(DeliveryDelayed(
                shipment_id=self.shipment_id,
                order_id=self.order_id,
                delay_days=delay.days
            ))

        self._publish_event(DeliveryCompleted(
            shipment_id=self.shipment_id,
            order_id=self.order_id,
            is_late=delay > timedelta(days=0)
        ))

    def _calculate_delay(self) -> timedelta:
        """Business rule: calculate delivery delay"""
        if not self._estimated_delivery or not self._actual_delivery:
            return timedelta(days=0)

        return self._actual_delivery - self._estimated_delivery
```

**Domain Events:**
- `ShipmentDispatched` → Sales Context (update order status)
- `DeliveryCompleted` → Sales Context, Customer Context
- `DeliveryDelayed` → Customer Context (compensate)

**Database Schema:**
```sql
-- core.shipments
CREATE TABLE core.shipments (
    shipment_id UUID PRIMARY KEY,
    order_id UUID NOT NULL,  -- No FK to Sales Context
    carrier_id UUID NOT NULL,
    shipped_at TIMESTAMP,
    estimated_delivery TIMESTAMP NOT NULL,
    actual_delivery TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    delay_days INT GENERATED ALWAYS AS (
        EXTRACT(DAY FROM (actual_delivery - estimated_delivery))
    ) STORED,
    is_late BOOLEAN GENERATED ALWAYS AS (
        actual_delivery > estimated_delivery
    ) STORED
);
```

---

### 3. Marketplace Context

**Responsibility:** Product catalog and seller management

**Bounded Context Definition:**
```
Marketplace Context owns:
- Product catalog and categorization
- Seller onboarding and management
- Product-seller associations
- Inventory tracking (future)

Marketplace Context does NOT own:
- Order items (Sales Context references products)
- Product reviews (Customer Context)
```

**Core Aggregates:**

```python
# domain/marketplace/aggregates/product.py
class Product:  # Aggregate Root
    """
    Invariants:
    - Product must belong to category
    - Dimensions must be positive
    - Weight must be positive
    """

    def __init__(
        self,
        product_id: ProductId,
        category: ProductCategory,
        dimensions: ProductDimensions
    ):
        self.product_id = product_id
        self._category = category
        self._dimensions = dimensions
        self._validate_invariants()

    def update_dimensions(self, dimensions: ProductDimensions):
        """Update physical dimensions"""
        self._dimensions = dimensions
        self._validate_invariants()

    def recategorize(self, new_category: ProductCategory):
        """Move to different category"""
        old_category = self._category
        self._category = new_category

        self._publish_event(ProductRecategorized(
            product_id=self.product_id,
            old_category=old_category,
            new_category=new_category
        ))

    def _validate_invariants(self):
        if self._dimensions.weight <= 0:
            raise InvariantViolation("Weight must be positive")

        if any(d <= 0 for d in [
            self._dimensions.length,
            self._dimensions.width,
            self._dimensions.height
        ]):
            raise InvariantViolation("Dimensions must be positive")

# domain/marketplace/value_objects.py
@dataclass(frozen=True)
class ProductDimensions:
    """Value object for product dimensions"""
    length: Decimal
    width: Decimal
    height: Decimal
    weight: Decimal

    def volume(self) -> Decimal:
        """Calculate shipping volume"""
        return self.length * self.width * self.height

    def __post_init__(self):
        if any(v <= 0 for v in [self.length, self.width, self.height, self.weight]):
            raise ValueError("All dimensions must be positive")
```

**Domain Events:**
- `ProductListed` → Sales Context (available for sale)
- `ProductDelisted` → Sales Context (no longer available)
- `SellerRegistered` → Customer Context (for seller reviews)

---

### 4. Customer Context

**Responsibility:** Customer profiles, reviews, and loyalty

**Bounded Context Definition:**
```
Customer Context owns:
- Customer profile and preferences
- Review submission and moderation
- Customer segmentation and loyalty
- Satisfaction tracking

Customer Context does NOT own:
- Order history (Sales Context)
- Delivery performance (Fulfillment Context)
```

**Core Aggregates:**

```python
# domain/customer/aggregates/customer.py
class Customer:  # Aggregate Root
    """
    Invariants:
    - Email must be valid and unique
    - Segment must be calculated from metrics
    - Loyalty points cannot be negative
    """

    def __init__(self, customer_id: CustomerId, email: Email, city: City):
        self.customer_id = customer_id
        self._email = email
        self._city = city
        self._metrics = CustomerMetrics()  # Value object
        self._segment = CustomerSegment.NEW

    def handle_order_completed(self, event: OrderCompleted):
        """React to order completion from Sales Context"""
        self._metrics = self._metrics.add_order(
            total=event.order_total,
            date=event.completed_at
        )

        # Recalculate segment based on new metrics
        new_segment = self._calculate_segment()
        if new_segment != self._segment:
            old_segment = self._segment
            self._segment = new_segment
            self._publish_event(CustomerSegmentChanged(
                customer_id=self.customer_id,
                old_segment=old_segment,
                new_segment=new_segment
            ))

    def submit_review(self, order_id: OrderId, score: ReviewScore, comment: str):
        """Submit review for completed order"""
        review = Review(
            customer_id=self.customer_id,
            order_id=order_id,
            score=score,
            comment=comment,
            submitted_at=datetime.now()
        )

        self._publish_event(ReviewSubmitted(
            review_id=review.review_id,
            customer_id=self.customer_id,
            order_id=order_id,
            score=score
        ))

        return review

    def _calculate_segment(self) -> CustomerSegment:
        """Business rule: customer segmentation"""
        if self._metrics.is_churned():
            return CustomerSegment.CHURNED

        if self._metrics.is_vip():
            return CustomerSegment.VIP

        if self._metrics.is_loyal():
            return CustomerSegment.LOYAL

        if self._metrics.total_orders == 1:
            return CustomerSegment.ONE_TIME

        if self._metrics.total_orders > 1:
            return CustomerSegment.REGULAR

        return CustomerSegment.NEW

# domain/customer/value_objects.py
@dataclass(frozen=True)
class CustomerMetrics:
    """Value object for customer metrics"""
    total_orders: int = 0
    total_spent: Money = Money(0)
    last_order_date: Optional[datetime] = None
    average_order_value: Money = Money(0)

    def add_order(self, total: Money, date: datetime) -> 'CustomerMetrics':
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
        """Business rule: VIP customer definition"""
        return self.total_orders > 5 and self.total_spent > Money(1000)

    def is_loyal(self) -> bool:
        """Business rule: Loyal customer definition"""
        return self.total_orders > 5

    def is_churned(self) -> bool:
        """Business rule: Churned customer definition"""
        if not self.last_order_date:
            return False

        days_since_last_order = (datetime.now() - self.last_order_date).days
        return days_since_last_order > 180
```

**Domain Events:**
- `CustomerRegistered` → Sales Context (available for orders)
- `ReviewSubmitted` → Marketplace Context (product/seller rating)
- `CustomerSegmentChanged` → Sales Context (targeted campaigns)

---

### 5. Shared Kernel

**Value Objects used across all contexts:**

```python
# shared_kernel/value_objects.py

@dataclass(frozen=True)
class Money:
    """Value object for monetary amounts"""
    amount: Decimal
    currency: str = "BRL"

    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, scalar: Decimal) -> 'Money':
        return Money(self.amount * scalar, self.currency)

    def __gt__(self, other: 'Money') -> bool:
        return self.amount > other.amount

@dataclass(frozen=True)
class Address:
    """Value object for Brazilian addresses"""
    zip_code: str
    city: str
    state: str

    def __post_init__(self):
        if len(self.zip_code) != 8:
            raise ValueError("Invalid Brazilian ZIP code")

        if self.state not in BRAZILIAN_STATES:
            raise ValueError(f"Invalid state: {self.state}")

@dataclass(frozen=True)
class Geolocation:
    """Value object for geographic coordinates"""
    latitude: Decimal
    longitude: Decimal

    def distance_to(self, other: 'Geolocation') -> Decimal:
        """Calculate distance in kilometers using Haversine formula"""
        # Implementation...
        pass

@dataclass(frozen=True)
class DateRange:
    """Value object for date ranges"""
    start: datetime
    end: datetime

    def __post_init__(self):
        if self.end < self.start:
            raise ValueError("End date must be after start date")

    def contains(self, date: datetime) -> bool:
        return self.start <= date <= self.end

    def duration_days(self) -> int:
        return (self.end - self.start).days
```

---

## Clean Architecture Layers

### Layer Dependency Rules

**The Dependency Rule:** Source code dependencies must point only inward, toward higher-level policies.

```
┌─────────────────────────────────────────────────┐
│         Frameworks & Drivers (Outermost)        │
│  PostgreSQL, CSV Files, Dagster, Marimo, dbt   │
└──────────────────┬──────────────────────────────┘
                   │ Implements
┌──────────────────▼──────────────────────────────┐
│        Interface Adapters (Adapters)            │
│  Repositories, Controllers, Presenters, Gateways│
└──────────────────┬──────────────────────────────┘
                   │ Uses
┌──────────────────▼──────────────────────────────┐
│         Application Business Rules               │
│  Use Cases, Application Services, DTOs          │
└──────────────────┬──────────────────────────────┘
                   │ Orchestrates
┌──────────────────▼──────────────────────────────┐
│        Enterprise Business Rules (Core)          │
│  Entities, Value Objects, Domain Events         │
└─────────────────────────────────────────────────┘
```

### Layer 1: Domain Layer (Core)

**Location:** `src/domain/`

**Responsibilities:**
- Define business entities and aggregates
- Enforce business rules and invariants
- Publish domain events
- Define repository interfaces (ports)

**Dependencies:** NONE (pure Python, no external libraries)

**Structure:**
```
src/domain/
├── sales/
│   ├── aggregates/
│   │   ├── order.py
│   │   └── payment.py
│   ├── value_objects.py
│   ├── events.py
│   └── repositories.py  # Interfaces only
├── customer/
│   ├── aggregates/
│   │   ├── customer.py
│   │   └── review.py
│   ├── value_objects.py
│   └── events.py
├── fulfillment/
│   └── ...
├── marketplace/
│   └── ...
└── shared_kernel/
    └── value_objects.py
```

**Example Repository Interface (Port):**
```python
# domain/sales/repositories.py
from abc import ABC, abstractmethod
from typing import Optional
from .aggregates.order import Order, OrderId

class OrderRepository(ABC):
    """Port: Interface for Order persistence"""

    @abstractmethod
    def get(self, order_id: OrderId) -> Optional[Order]:
        """Retrieve order by ID"""
        pass

    @abstractmethod
    def save(self, order: Order) -> None:
        """Persist order (insert or update)"""
        pass

    @abstractmethod
    def delete(self, order_id: OrderId) -> None:
        """Delete order"""
        pass
```

---

### Layer 2: Application Layer

**Location:** `src/application/`

**Responsibilities:**
- Implement use cases (business workflows)
- Coordinate between domain objects
- Transaction management
- Emit integration events

**Dependencies:** Domain layer only

**Structure:**
```
src/application/
├── sales/
│   ├── use_cases/
│   │   ├── place_order.py
│   │   ├── process_payment.py
│   │   └── cancel_order.py
│   ├── services/
│   │   └── order_service.py
│   └── dtos/
│       └── order_dto.py
├── customer/
│   └── ...
└── shared/
    ├── event_bus.py
    └── unit_of_work.py
```

**Example Use Case:**
```python
# application/sales/use_cases/place_order.py
from dataclasses import dataclass
from typing import List
from domain.sales.aggregates.order import Order, OrderId
from domain.sales.repositories import OrderRepository
from domain.customer.repositories import CustomerRepository
from application.shared.event_bus import EventBus

@dataclass
class PlaceOrderCommand:
    """DTO for placing order"""
    customer_id: str
    items: List[dict]  # [{product_id, price, freight}, ...]

class PlaceOrderUseCase:
    """Use case: Place new order"""

    def __init__(
        self,
        order_repo: OrderRepository,
        customer_repo: CustomerRepository,
        event_bus: EventBus
    ):
        self.order_repo = order_repo
        self.customer_repo = customer_repo
        self.event_bus = event_bus

    def execute(self, command: PlaceOrderCommand) -> OrderId:
        # Validate customer exists
        customer = self.customer_repo.get(command.customer_id)
        if not customer:
            raise CustomerNotFoundError(command.customer_id)

        # Create order (domain logic)
        order = Order.create_new(customer_id=command.customer_id)

        # Add items (validates invariants)
        for item_data in command.items:
            order.add_item(
                product_id=item_data['product_id'],
                price=Money(item_data['price']),
                freight=Money(item_data['freight'])
            )

        # Persist
        self.order_repo.save(order)

        # Publish events
        for event in order.domain_events:
            self.event_bus.publish(event)

        return order.order_id
```

---

### Layer 3: Infrastructure Layer (Adapters)

**Location:** `src/infrastructure/`

**Responsibilities:**
- Implement repository interfaces (adapters)
- Database access (PostgreSQL)
- External data sources (CSV, API)
- Orchestration framework integration
- Event publishing mechanisms

**Dependencies:** Domain, Application, External libraries

**Structure:**
```
src/infrastructure/
├── persistence/
│   ├── postgresql/
│   │   ├── repositories/
│   │   │   ├── order_repository.py  # Implements domain interface
│   │   │   └── customer_repository.py
│   │   ├── mappers/
│   │   │   └── order_mapper.py  # ORM ↔ Domain
│   │   └── models.py  # SQLAlchemy models
│   └── duckdb/  # Alternative adapter (same interface)
│       └── repositories/
├── data_sources/
│   ├── csv_adapter.py
│   ├── s3_adapter.py
│   └── api_adapter.py
├── orchestration/
│   ├── dagster/
│   │   ├── assets.py
│   │   └── jobs.py
│   └── airflow/  # Alternative
│       └── dags.py
└── messaging/
    ├── event_publisher.py
    └── message_queue.py
```

**Example Repository Implementation (Adapter):**
```python
# infrastructure/persistence/postgresql/repositories/order_repository.py
from typing import Optional
from sqlalchemy.orm import Session
from domain.sales.aggregates.order import Order, OrderId
from domain.sales.repositories import OrderRepository  # Port
from .mappers.order_mapper import OrderMapper

class PostgreSQLOrderRepository(OrderRepository):
    """Adapter: PostgreSQL implementation of OrderRepository"""

    def __init__(self, session: Session):
        self.session = session
        self.mapper = OrderMapper()

    def get(self, order_id: OrderId) -> Optional[Order]:
        """Retrieve order from PostgreSQL"""
        orm_order = self.session.query(OrderModel)\
            .filter_by(order_id=str(order_id))\
            .first()

        if not orm_order:
            return None

        # Map ORM model to domain aggregate
        return self.mapper.to_domain(orm_order)

    def save(self, order: Order) -> None:
        """Persist order to PostgreSQL"""
        # Map domain aggregate to ORM model
        orm_order = self.mapper.to_orm(order)

        # Upsert with optimistic locking
        self.session.merge(orm_order)
        self.session.commit()
```

**Example Data Source Adapter:**
```python
# infrastructure/data_sources/csv_adapter.py
from pathlib import Path
from typing import Iterator
from domain.sales.value_objects import OrderData
from application.ports.data_source import DataSource  # Port

class CSVDataSource(DataSource):
    """Adapter: Read data from CSV files"""

    def __init__(self, base_path: Path):
        self.base_path = base_path

    def read_orders(self) -> Iterator[OrderData]:
        """Read orders from CSV"""
        csv_path = self.base_path / "orders.csv"

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield OrderData(
                    order_id=row['order_id'],
                    customer_id=row['customer_id'],
                    status=row['order_status'],
                    # ... map CSV columns to domain objects
                )
```

**Example Orchestration Adapter:**
```python
# infrastructure/orchestration/dagster/assets.py
from dagster import asset, AssetExecutionContext
from dependency_injection import get_use_case  # DI container

@asset(group_name="sales")
def load_orders(context: AssetExecutionContext):
    """Dagster asset: Thin adapter to use case"""

    # Get use case from DI container (not instantiated here)
    use_case = get_use_case(LoadOrdersUseCase)

    # Execute business logic
    result = use_case.execute()

    # Return Dagster metadata
    return MaterializeResult(
        metadata={
            "orders_loaded": result.count,
            "duration_seconds": result.duration
        }
    )
```

---

### Layer 4: Presentation Layer

**Location:** `src/presentation/`

**Responsibilities:**
- Dashboards (Marimo notebooks)
- REST/GraphQL APIs
- CLI tools
- Report generators

**Dependencies:** Application layer

**Structure:**
```
src/presentation/
├── api/
│   ├── rest/
│   │   ├── routes/
│   │   │   ├── orders.py
│   │   │   └── customers.py
│   │   └── app.py
│   └── graphql/
│       └── schema.py
├── dashboards/
│   ├── executive_dashboard.py  # Marimo notebook
│   └── sales_analytics.py
└── cli/
    └── commands.py
```

**Example API Controller:**
```python
# presentation/api/rest/routes/orders.py
from fastapi import APIRouter, Depends
from application.sales.use_cases.place_order import PlaceOrderUseCase
from .dependencies import get_place_order_use_case

router = APIRouter(prefix="/orders")

@router.post("/")
async def create_order(
    command: PlaceOrderCommand,
    use_case: PlaceOrderUseCase = Depends(get_place_order_use_case)
):
    """REST endpoint: Create new order"""
    try:
        order_id = use_case.execute(command)
        return {"order_id": str(order_id)}
    except DomainException as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Technology Stack

### Core Decision: PostgreSQL (Not DuckDB for MVP)

**Rationale:**
After analyzing the challenge report's critique of the "database portability myth," we choose PostgreSQL upfront for these reasons:

1. **Production-ready features needed from day 1:**
   - Full ACID transactions (SCD Type 2, if used)
   - Connection pooling (PgBouncer)
   - Row-level security for authorization
   - Mature replication (streaming, logical)
   - Rich extension ecosystem (PostGIS for geolocation)

2. **Team capability:**
   - PostgreSQL is more common than DuckDB
   - Better documentation and community
   - More hiring options

3. **Future-proofing:**
   - If we need ClickHouse later, migration is explicit
   - No pretending databases are interchangeable
   - Clear migration path (see Technology Decision Matrix)

**Trade-off accepted:**
- More complex setup than DuckDB
- Requires database server management
- Higher operational overhead

**Migration escape hatch:**
- If data exceeds 1TB or queries exceed SLA, evaluate ClickHouse
- Migration requires complete schema redesign (not "minimal changes")
- Estimated migration effort: 8-12 weeks

### Technology Stack Matrix

| Layer | Technology | Purpose | Alternatives | Lock-in Risk |
|-------|-----------|---------|--------------|--------------|
| **Database** | PostgreSQL 16 | Primary data store | ClickHouse, Snowflake | Medium (SQL standard) |
| **ORM** | SQLAlchemy 2.0 | Object-relational mapping | None (raw SQL) | Low (can remove) |
| **Transformation** | dbt Core 1.7 | SQL transformations | Custom SQL scripts | Medium (can migrate) |
| **Orchestration** | Dagster 1.5 | Workflow scheduling | Airflow, Prefect | Low (adapter pattern) |
| **Language** | Python 3.11 | Business logic | None | None |
| **Testing** | pytest | Unit/integration tests | None | None |
| **Data Quality** | Great Expectations | Quality checks | Custom framework | Low (can replace) |
| **Analytics** | Marimo | Interactive notebooks | Jupyter, Streamlit | Low (can replace) |
| **Monitoring** | Prometheus + Grafana | Observability | DataDog, New Relic | Medium |
| **Version Control** | Git | Code versioning | None | None |
| **CI/CD** | GitHub Actions | Automation | GitLab CI, Jenkins | Low |
| **Schema Migration** | Alembic | Database migrations | Flyway, Liquibase | Low |

### Dependency Management

**Configuration Management:**
```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings (from env or .env file)"""

    # Database
    database_url: str
    database_pool_size: int = 10

    # Data sources
    csv_data_path: Path
    s3_bucket: Optional[str] = None

    # Security
    encryption_key: str
    jwt_secret: str

    # Observability
    log_level: str = "INFO"
    metrics_port: int = 9090

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

**Dependency Injection:**
```python
# infrastructure/di_container.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    """Dependency injection container"""

    # Configuration
    config = providers.Singleton(Settings)

    # Database
    db_session = providers.Factory(
        create_db_session,
        connection_string=config.provided.database_url
    )

    # Repositories
    order_repository = providers.Factory(
        PostgreSQLOrderRepository,
        session=db_session
    )

    # Use cases
    place_order_use_case = providers.Factory(
        PlaceOrderUseCase,
        order_repo=order_repository,
        event_bus=event_bus
    )
```

---

## Security Architecture

### Authentication

**System:** JWT-based authentication

```python
# infrastructure/security/authentication.py
from datetime import datetime, timedelta
import jwt

class AuthenticationService:
    """Handle user authentication"""

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Verify credentials and return user"""
        # Hash password and compare
        user = self.user_repo.get_by_username(username)
        if not user:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        return user

    def generate_token(self, user: User) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': str(user.user_id),
            'roles': [r.name for r in user.roles],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }

        return jwt.encode(payload, self.settings.jwt_secret, algorithm='HS256')
```

### Authorization

**Model:** Role-Based Access Control (RBAC)

```python
# domain/security/authorization.py
from enum import Enum

class Role(Enum):
    """User roles"""
    ADMIN = "admin"
    DATA_ENGINEER = "data_engineer"
    ANALYST = "analyst"
    VIEWER = "viewer"

class Permission(Enum):
    """Permissions"""
    READ_ORDERS = "read:orders"
    WRITE_ORDERS = "write:orders"
    READ_CUSTOMERS = "read:customers"
    WRITE_CUSTOMERS = "write:customers"
    MANAGE_USERS = "manage:users"

ROLE_PERMISSIONS = {
    Role.ADMIN: [Permission.MANAGE_USERS, ...],  # All permissions
    Role.DATA_ENGINEER: [Permission.WRITE_ORDERS, Permission.WRITE_CUSTOMERS, ...],
    Role.ANALYST: [Permission.READ_ORDERS, Permission.READ_CUSTOMERS],
    Role.VIEWER: [Permission.READ_ORDERS]  # Read-only
}
```

**Row-Level Security (PostgreSQL):**
```sql
-- Enable RLS on sensitive tables
ALTER TABLE core.customers ENABLE ROW LEVEL SECURITY;

-- Policy: Analysts can only see customers from their region
CREATE POLICY analyst_region_policy ON core.customers
    FOR SELECT
    TO analyst_role
    USING (customer_state = current_setting('app.user_region'));

-- Policy: Admins see everything
CREATE POLICY admin_full_access ON core.customers
    FOR ALL
    TO admin_role
    USING (true);
```

### Encryption

**At Rest:**
- PostgreSQL Transparent Data Encryption (TDE) for data files
- Encrypted backups (AES-256)
- Separate encryption keys for PII fields

**In Transit:**
- TLS 1.3 for all database connections
- HTTPS for all API endpoints
- VPN for admin access

**Application-Level Encryption:**
```python
# infrastructure/security/encryption.py
from cryptography.fernet import Fernet

class EncryptionService:
    """Encrypt sensitive data at application level"""

    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key.encode())

    def encrypt_pii(self, plaintext: str) -> str:
        """Encrypt PII (emails, addresses)"""
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt_pii(self, ciphertext: str) -> str:
        """Decrypt PII"""
        return self.cipher.decrypt(ciphertext.encode()).decode()
```

### PII Handling (LGPD Compliance)

**LGPD (Lei Geral de Proteção de Dados):** Brazilian data protection law similar to GDPR

**PII Fields Identified:**
- Customer email
- Customer address (city, state, zip code)
- Review comments (may contain personal info)

**Compliance Measures:**

1. **Data Minimization:**
   ```python
   # Only collect necessary PII
   class CustomerProfile:
       email: str  # Required for communication
       city: str   # Required for logistics
       # NOT collected: phone, full address, CPF (tax ID)
   ```

2. **Right to Erasure:**
   ```python
   # application/customer/use_cases/anonymize_customer.py
   class AnonymizeCustomerUseCase:
       """LGPD: Right to be forgotten"""

       def execute(self, customer_id: CustomerId):
           customer = self.customer_repo.get(customer_id)

           # Anonymize PII but keep aggregates for analytics
           customer.anonymize()  # email → "anonymized@example.com"

           # Delete reviews
           self.review_repo.delete_by_customer(customer_id)

           # Keep order history but anonymize
           orders = self.order_repo.get_by_customer(customer_id)
           for order in orders:
               order.anonymize_customer_data()
   ```

3. **Consent Management:**
   ```sql
   -- Track consent for data usage
   CREATE TABLE core.customer_consents (
       consent_id UUID PRIMARY KEY,
       customer_id UUID NOT NULL,
       purpose VARCHAR(100) NOT NULL,  -- 'marketing', 'analytics', etc.
       granted BOOLEAN NOT NULL,
       granted_at TIMESTAMP,
       revoked_at TIMESTAMP
   );
   ```

4. **Data Retention:**
   - Active customers: Unlimited
   - Inactive customers (> 2 years): Anonymize email/address
   - Deleted accounts: Anonymize immediately, delete after 30 days

### Audit Logging

**Log all data access:**
```python
# infrastructure/security/audit_logger.py
class AuditLogger:
    """Log all data access for compliance"""

    def log_access(
        self,
        user_id: str,
        action: str,
        resource: str,
        resource_id: str,
        success: bool
    ):
        """Log data access event"""
        log_entry = AuditLogEntry(
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,  # 'read', 'write', 'delete'
            resource=resource,  # 'customer', 'order'
            resource_id=resource_id,
            success=success,
            ip_address=get_client_ip()
        )

        # Write to append-only audit log (separate database)
        self.audit_repo.append(log_entry)
```

**Audit Log Schema:**
```sql
-- Separate database for audit logs (not in main DW)
CREATE TABLE audit.access_logs (
    log_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    user_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL,
    resource VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100) NOT NULL,
    success BOOLEAN NOT NULL,
    ip_address INET,
    CONSTRAINT immutable_audit_log CHECK (false)  -- Prevent updates/deletes
);

-- Append-only: Disable updates/deletes
REVOKE UPDATE, DELETE ON audit.access_logs FROM ALL;
```

---

## Data Architecture

### Schema Organization

**Three layers (not four like V1):**

1. **Staging Layer** (`staging` schema)
   - Raw data loaded from sources
   - Minimal transformation
   - 1:1 mapping to source files
   - Retained for 30 days

2. **Core Layer** (`core` schema)
   - Dimensional model (star schema)
   - Business logic applied
   - SCD Type 1 by default
   - Source of truth

3. **Mart Layer** (`mart` schema)
   - Pre-aggregated for specific use cases
   - Optimized for query performance
   - Refreshed on schedule

**Removed:** `raw` layer (staging serves same purpose)

### Dimensional Model (Simplified)

**Star Schema:**
```
         ┌─────────────┐
         │ dim_customer│
         └──────┬──────┘
                │
                │
         ┌──────▼──────┐      ┌─────────────┐
         │             │◀─────┤ dim_product │
         │ fact_order_ │      └─────────────┘
         │    items    │
         │             │◀─────┬─────────────┐
         └──────┬──────┘      │ dim_seller  │
                │             └─────────────┘
                │
         ┌──────▼──────┐
         │  dim_date   │
         └─────────────┘
```

**Dimensions (SCD Type 1 for MVP):**
- `dim_customer` - Customer profiles
- `dim_product` - Product catalog
- `dim_seller` - Seller information
- `dim_date` - Date dimension (generated)

**Facts:**
- `fact_order_items` - Order line items (transactional grain)
- `fact_orders` - Order summary (order grain)
- `fact_deliveries` - Delivery performance (shipment grain)

**Why SCD Type 1:**
- Simpler queries (no time-based joins)
- Better performance (fewer rows)
- Sufficient for most analytics
- Can add Type 2 later if justified

### Schema Evolution Strategy

**Approach:** Backward-compatible changes only

```python
# infrastructure/schema_evolution/schema_registry.py
from enum import Enum

class CompatibilityMode(Enum):
    BACKWARD = "backward"  # New schema can read old data
    FORWARD = "forward"    # Old schema can read new data
    FULL = "full"          # Both directions
    NONE = "none"          # Breaking change

class SchemaRegistry:
    """Track schema versions and compatibility"""

    def register_schema(
        self,
        table: str,
        version: int,
        schema: dict,
        compatibility: CompatibilityMode
    ):
        """Register new schema version"""

        # Validate compatibility
        if compatibility != CompatibilityMode.NONE:
            previous_schema = self.get_schema(table, version - 1)
            if not self.is_compatible(previous_schema, schema, compatibility):
                raise IncompatibleSchemaError(
                    f"Schema v{version} is incompatible with v{version-1}"
                )

        # Store schema
        self.schema_repo.save(SchemaVersion(
            table=table,
            version=version,
            schema=schema,
            compatibility=compatibility,
            registered_at=datetime.now()
        ))
```

**Migration Strategy (Alembic):**
```python
# migrations/versions/001_add_customer_segment.py
"""Add customer_segment column to dim_customer

Revision ID: 001
Revises: None
Create Date: 2025-11-09
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    """Add new column with default value (backward compatible)"""
    op.add_column(
        'dim_customer',
        sa.Column(
            'customer_segment',
            sa.String(20),
            nullable=True,  # Allow NULL initially
            server_default='NEW'  # Default for existing rows
        )
    )

    # Backfill using domain logic
    op.execute("""
        UPDATE core.dim_customer
        SET customer_segment = calculate_segment(total_orders, total_spent, last_order_date)
    """)

    # Now make NOT NULL
    op.alter_column('dim_customer', 'customer_segment', nullable=False)

def downgrade():
    """Remove column (rollback)"""
    op.drop_column('dim_customer', 'customer_segment')
```

---

## Deployment Model

### Environments

1. **Development** - Local developer machines
2. **CI/CD** - GitHub Actions runners
3. **Staging** - Pre-production testing
4. **Production** - Live system

### Infrastructure as Code (IaC)

**Docker Compose for local development:**
```yaml
# docker-compose.yml
version: '3.9'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: olist_dw
      POSTGRES_USER: olist
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  dagster:
    build: .
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://olist:${DB_PASSWORD}@postgres:5432/olist_dw
    ports:
      - "3000:3000"

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    depends_on:
      - prometheus
    ports:
      - "3001:3000"

volumes:
  postgres_data:
```

### Deployment Pipeline

```
┌──────────────┐
│  Git Push    │
│  to main     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Run Tests   │
│  (pytest)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Build Docker │
│   Image      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Deploy to    │
│  Staging     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Run Smoke    │
│   Tests      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Manual       │
│ Approval     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Deploy to    │
│ Production   │
└──────────────┘
```

**GitHub Actions Workflow:**
```yaml
# .github/workflows/deploy.yml
name: Deploy Data Warehouse

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: pytest tests/unit
      - name: Run integration tests
        run: pytest tests/integration
      - name: Run data quality tests
        run: great_expectations checkpoint run daily_quality_check

  deploy-staging:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: ./scripts/deploy.sh staging
      - name: Run smoke tests
        run: pytest tests/smoke --env=staging

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    steps:
      - name: Deploy to production
        run: ./scripts/deploy.sh production
```

---

## Disaster Recovery

### Backup Strategy

**Full backups:**
- Frequency: Daily at 2 AM
- Retention: 30 days
- Storage: S3 with versioning enabled

**Incremental backups:**
- Frequency: Every 4 hours
- Retention: 7 days
- Storage: S3

**WAL archiving:**
- Continuous archive to S3
- Point-in-time recovery (PITR) capability

**Backup Script:**
```bash
#!/bin/bash
# scripts/backup.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="olist_dw_${TIMESTAMP}.sql.gz"

# Create backup
pg_dump \
  --host=postgres \
  --username=olist \
  --format=custom \
  --compress=9 \
  olist_dw | gzip > "/tmp/${BACKUP_FILE}"

# Upload to S3
aws s3 cp "/tmp/${BACKUP_FILE}" "s3://olist-backups/daily/${BACKUP_FILE}"

# Verify backup integrity
pg_restore --list "/tmp/${BACKUP_FILE}" > /dev/null

# Cleanup local file
rm "/tmp/${BACKUP_FILE}"

echo "Backup completed: ${BACKUP_FILE}"
```

### Recovery Procedures

**Scenario 1: Data corruption in single table**
```sql
-- Restore from snapshot (PostgreSQL)
BEGIN;
  DROP TABLE core.dim_customer;
  CREATE TABLE core.dim_customer AS
    SELECT * FROM core.dim_customer_snapshot_20251108;
COMMIT;
```

**Scenario 2: Point-in-time recovery**
```bash
# Restore to specific timestamp
pg_restore \
  --dbname=olist_dw_recovery \
  --create \
  /backups/olist_dw_20251108.backup

# Apply WAL up to target time
pg_waldump --end-time='2025-11-08 14:30:00'
```

**Scenario 3: Complete database loss**
1. Provision new PostgreSQL instance
2. Restore latest full backup
3. Apply WAL archives since backup
4. Validate data integrity
5. Redirect application traffic

**Recovery Time Objective (RTO):** 2 hours
**Recovery Point Objective (RPO):** 1 hour

### Rollback Procedures

**Code rollback:**
```bash
# Rollback to previous version
git revert HEAD
git push

# Redeploy
./scripts/deploy.sh production
```

**Schema rollback:**
```bash
# Alembic downgrade
alembic downgrade -1

# Or specific version
alembic downgrade abc123
```

**Data rollback:**
```sql
-- Blue/green deployment: Switch to previous version
UPDATE core.metadata
SET active_version = 'v1.2.0'
WHERE active_version = 'v1.3.0';

-- Views automatically switch to v1.2.0 tables
```

---

## Cost Analysis (Realistic)

### Infrastructure Costs (Annual)

| Component | Tier | Cost/Month | Cost/Year | Notes |
|-----------|------|------------|-----------|-------|
| **PostgreSQL** | AWS RDS db.t3.medium | $80 | $960 | 2 vCPU, 4GB RAM |
| **Storage** | 100 GB SSD | $12 | $144 | Grows ~5GB/month |
| **Backups** | S3 Standard | $5 | $60 | 200 GB retained |
| **Compute (Dagster)** | EC2 t3.small | $20 | $240 | Orchestration |
| **Monitoring** | Grafana Cloud Free | $0 | $0 | < 10k metrics |
| **Total Infrastructure** | | **$117** | **$1,404** | |

### Development Costs

| Phase | Duration | Team | Cost | Notes |
|-------|----------|------|------|-------|
| **Phase 0: Foundation** | 4 weeks | 1 architect + 1 engineer | $18,000 | Domain modeling, architecture |
| **Phase 1: Core** | 8 weeks | 2 engineers | $36,000 | Sales + Customer contexts |
| **Phase 2: Expansion** | 6 weeks | 2 engineers | $27,000 | Fulfillment + Marketplace |
| **Phase 3: Production** | 4 weeks | 2 engineers | $18,000 | Hardening, deployment |
| **Total Development** | 22 weeks | | **$99,000** | |
| **Contingency (20%)** | | | **$20,000** | Realistic buffer |
| **Grand Total** | | | **$119,000** | |

### Ongoing Costs (Annual)

| Category | Cost/Year | Notes |
|----------|-----------|-------|
| Infrastructure | $1,404 | AWS costs |
| Maintenance (20% of dev) | $19,800 | Bug fixes, updates |
| Monitoring & Alerts | $600 | PagerDuty, etc. |
| Training | $2,000 | Team upskilling |
| **Total Year 1** | **$23,804** | |
| **Total Year 2+** | **$23,804** | Stable state |

### Cost Comparison with V1

| | V1 (Claimed) | V1 (Actual) | V2 (Realistic) |
|---|--------------|-------------|----------------|
| **Initial Development** | $51,500 | $150,000 (with rework) | $119,000 |
| **Infrastructure (Year 1)** | Included | $1,500 | $1,404 |
| **Maintenance (Year 1)** | Not estimated | $30,000 | $19,800 |
| **Total Cost of Ownership (3 years)** | $51,500 | $240,000 | $190,000 |

**V2 saves $50,000 over 3 years by doing it right the first time.**

---

## Conclusion

This architecture addresses all 8 critical flaws identified in the challenge report:

1. **No Database Portability Myth** - PostgreSQL chosen upfront
2. **Rich Domain Model** - Business logic in aggregates, not SQL
3. **Clear Bounded Contexts** - 4 contexts with explicit boundaries
4. **Explicit Dependencies** - Ports & Adapters, dependency injection
5. **Aggregate Protection** - Invariants enforced at domain layer
6. **Simplified SCD** - Type 1 by default, Type 2 only if justified
7. **Data Quality as Domain** - Quality bounded context (see dedicated doc)
8. **Orchestration Decoupled** - Dagster as thin adapter

**Next Steps:**
1. Review and approve this architecture
2. Conduct domain modeling workshop (Phase 0)
3. Set up development environment
4. Begin implementation following roadmap

---

**Document End**
