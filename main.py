from src.pipeline import run_pipeline


if __name__ == "__main__":
    results = run_pipeline()

    print("\n" + "=" * 80)
    print("PIPELINE RESULTS")
    print("=" * 80)

    for index, result in enumerate(results, start=1):
        file_info = result.get("file", {})

        print(
            f"{index}. "
            f"{file_info.get('name')} | "
            f"{file_info.get('type')} | "
            f"{result.get('content_type')}"
        )

    print("\n" + "=" * 80)
    print(f"Pipeline completed: {len(results)} files processed.")
    print("=" * 80)