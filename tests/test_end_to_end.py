from src.pipeline import ProcessingPipeline


text = """
Patient Name: Ahmed Ali
Date of Birth: 1985-03-15
Gender: Male
Mobile: 01012345678

Diagnosis: Migraine
Patient reports headache for 3 days.

Blood Pressure: 120/80
Heart Rate: 75
Temperature: 37.2 C
Weight: 82 kg

Hemoglobin: 13.5 g/dL
Reference Range: 12 - 16 g/dL

Medication: Metformin
Dosage: 500 mg
Frequency: Twice daily
"""

pipeline = ProcessingPipeline()

result = pipeline.process_and_save(text)

print(result)