from src.pipeline import ProcessingPipeline


def main():
    pipeline = ProcessingPipeline()

    text = """
    Patient Name: Ahmed Ali
    Date of Birth: 1985-03-15
    Gender: Male
    Phone: 01012345678

    Visit Date: 2026-09-20
    Diagnosis: Migraine
    Clinical Notes: Patient reports headache for 3 days.

    Blood Pressure: 120/80 mmHg
    Heart Rate: 75
    Temperature: 37.2 C
    Weight: 82 kg

    Laboratory Test: Hemoglobin
    Result: 13.5 g/dL
    Reference Range: 12 - 16 g/dL
    Test Date: 2026-09-20

    Medication: Metformin
    Dosage: 500 mg
    Frequency: Twice daily
    """

    result = pipeline.process_text(text)

    print("\nPIPELINE RESULT:\n")
    print(result)


if __name__ == "__main__":
    main()