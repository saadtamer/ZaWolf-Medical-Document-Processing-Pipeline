from typing import Optional, List
from pydantic import BaseModel


class LocationData(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class StaffData(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    license_no: Optional[str] = None
    location_name: Optional[str] = None
    is_active: Optional[bool] = None


class ClientData(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    lead_source: Optional[str] = None
    medical_alerts: Optional[str] = None
    opt_in_sms: Optional[bool] = None


class MedicalHistoryData(BaseModel):
    type: Optional[str] = None
    name: Optional[str] = None
    notes: Optional[str] = None
    recorded_at: Optional[str] = None


class VitalData(BaseModel):
    blood_pressure: Optional[str] = None
    heart_rate: Optional[float] = None
    temperature: Optional[float] = None
    weight: Optional[float] = None
    recorded_at: Optional[str] = None


class LabResultData(BaseModel):
    test_name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    test_date: Optional[str] = None


class MedicationData(BaseModel):
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ServiceData(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    duration_min: Optional[int] = None
    price: Optional[float] = None


class AppointmentData(BaseModel):
    client_name: Optional[str] = None
    staff_name: Optional[str] = None
    location_name: Optional[str] = None
    service_name: Optional[str] = None
    room: Optional[str] = None
    start_at: Optional[str] = None
    end_at: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class TreatmentRecordData(BaseModel):
    appointment_id: Optional[int] = None
    product_name: Optional[str] = None
    units: Optional[float] = None
    lot_number: Optional[str] = None
    expiry_date: Optional[str] = None
    area: Optional[str] = None
    injection_sites: Optional[str] = None
    depth: Optional[str] = None
    device_settings: Optional[str] = None
    skin_response: Optional[str] = None
    aftercare: Optional[str] = None


class ConsentData(BaseModel):
    appointment_id: Optional[int] = None
    consent_type: Optional[str] = None
    signed_at: Optional[str] = None
    file_ref: Optional[str] = None


class PhotoData(BaseModel):
    treatment_id: Optional[int] = None
    type: Optional[str] = None
    taken_at: Optional[str] = None
    file_ref: Optional[str] = None


class InvoiceData(BaseModel):
    appointment_id: Optional[int] = None
    issue_date: Optional[str] = None
    subtotal: Optional[float] = None
    discount: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    status: Optional[str] = None


class InvoiceItemData(BaseModel):
    invoice_id: Optional[int] = None
    item_type: Optional[str] = None
    item_id: Optional[int] = None
    description: Optional[str] = None
    qty: Optional[float] = None
    unit_price: Optional[float] = None
    line_total: Optional[float] = None


class PaymentData(BaseModel):
    invoice_id: Optional[int] = None
    amount: Optional[float] = None
    method: Optional[str] = None
    paid_at: Optional[str] = None
    reference: Optional[str] = None


class PackageData(BaseModel):
    name: Optional[str] = None
    sessions_count: Optional[int] = None
    price: Optional[float] = None
    validity_days: Optional[int] = None


class ClientPackageData(BaseModel):
    package_name: Optional[str] = None
    remaining_sessions: Optional[int] = None
    expires_at: Optional[str] = None


class ProductData(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    type: Optional[str] = None
    unit: Optional[str] = None
    stock_qty: Optional[float] = None
    cost: Optional[float] = None
    price: Optional[float] = None


class SourceDocumentData(BaseModel):
    file_name: Optional[str] = None
    doc_type: Optional[str] = None
    ocr_text: Optional[str] = None
    llm_json: Optional[dict] = None
    confidence: Optional[float] = None
    review_status: Optional[str] = None


class LLMExtractionResult(BaseModel):
    locations: List[LocationData] = []
    staff: List[StaffData] = []
    clients: List[ClientData] = []
    medical_history: List[MedicalHistoryData] = []
    vitals: List[VitalData] = []
    lab_results: List[LabResultData] = []
    medications: List[MedicationData] = []
    services: List[ServiceData] = []
    appointments: List[AppointmentData] = []
    treatment_records: List[TreatmentRecordData] = []
    consents: List[ConsentData] = []
    photos: List[PhotoData] = []
    invoices: List[InvoiceData] = []
    invoice_items: List[InvoiceItemData] = []
    payments: List[PaymentData] = []
    packages: List[PackageData] = []
    client_packages: List[ClientPackageData] = []
    products: List[ProductData] = []
    source_documents: List[SourceDocumentData] = []