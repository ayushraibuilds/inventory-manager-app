from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional

class ItemDescriptor(BaseModel):
    name: str
    code: str
    short_desc: str
    long_desc: str
    images: List[str]

class ItemPrice(BaseModel):
    currency: str
    value: str
    maximum_value: str

class ItemQuantity(BaseModel):
    available: Dict[str, int]
    maximum: Dict[str, int]

class CatalogItem(BaseModel):
    id: str
    descriptor: ItemDescriptor
    price: ItemPrice
    quantity: ItemQuantity
    category_id: str
    
    # Allow extra fields just in case ONDC schema evolves
    model_config = ConfigDict(extra="allow")

class Provider(BaseModel):
    id: str
    descriptor: Dict[str, Any]
    items: List[CatalogItem]
    
    model_config = ConfigDict(extra="allow")

class BppCatalog(BaseModel):
    bpp_providers: List[Provider]
    
class CatalogResponse(BaseModel):
    bpp_catalog: Dict[str, Any] # Usually contains bpp/providers

class Pagination(BaseModel):
    total_count: int
    limit: int
    offset: int
    total_value: float
    low_stock_count: int

class PaginatedCatalogResponse(BaseModel):
    bpp_catalog: Dict[str, Any] = Field(alias="bpp/catalog")
    pagination: Pagination
    
    model_config = ConfigDict(populate_by_name=True)

class PriceCheckResponse(BaseModel):
    seller_id: str
    total_items: int
    suggestions: List[Dict[str, Any]]

class Order(BaseModel):
    id: str
    status: str
    created_at: str
    items: List[Dict[str, Any]]
    billing: Dict[str, Any]
    fulfillment: Dict[str, Any]
    quote: Dict[str, Any]
    
    model_config = ConfigDict(extra="allow")
    
class OrdersResponse(BaseModel):
    orders: List[Order]

class OrderCreateResponse(BaseModel):
    status: str
    order_id: str

class OrderStatusResponse(BaseModel):
    status: str
    order_status: str

class SellerProfile(BaseModel):
    id: str
    store_name: str
    phone: str
    email: Optional[str] = None
    upi_id: Optional[str] = None
    low_stock_alerts: bool = True
    created_at: Optional[str] = None
    billing_plan: Optional[str] = "free"
    billing_status: Optional[str] = "active"
    billing_interval: Optional[str] = "month"
    billing_provider: Optional[str] = None
    billing_email: Optional[str] = None
    razorpay_customer_id: Optional[str] = None
    razorpay_subscription_id: Optional[str] = None
    plan_started_at: Optional[str] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")

class SellerListResponse(BaseModel):
    sellers: List[SellerProfile]

class SellerProfileResponse(BaseModel):
    profile: Optional[SellerProfile] = None

class SellerProfileUpdateResponse(BaseModel):
    status: str
    profile: Optional[SellerProfile] = None

class OndcStatusEndpoints(BaseModel):
    on_search: str
    subscribe: str
    status: str

class OndcStatusResponse(BaseModel):
    status: str
    bpp_id: str
    bpp_uri: str
    protocol_version: str
    domain: str
    registered_sellers: int
    endpoints: OndcStatusEndpoints

class OndcSearchResponse(BaseModel):
    context: Dict[str, Any]
    message: Dict[str, Any]
    
class OndcSubscribeResponse(BaseModel):
    status: str
    message: str
    subscriber_id: str
    bpp_id: str
    note: str
