# Rice disease identification

## Run the local app

The app runs with Python and Streamlit, independently of XAMPP.

1. In PowerShell at this project folder, run `python -m venv .venv` if the environment does not exist.
2. Install packages: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
3. Start: `.\.venv\Scripts\python.exe -m streamlit run app.py`.
4. Open `http://localhost:8501`.
5. Download `rice_baseline.keras` and `class_names.json` from Google Drive's `rice-project/models` folder. Select both in the sidebar, or put them in this project's `models/` folder.
6. Upload a JPG or PNG rice photo and click **Check leaf**.

The app preserves saved class order and uses raw 0–255 RGB pixels because MobileNet preprocessing is already embedded in the Colab model. It uses inference mode, so augmentation is disabled. Keep both model files from the same training run. Photos are processed in memory and not written to disk by the app. Use only trusted model files. Model version compatibility must be checked with the actual Colab export; if loading fails, match TensorFlow/Keras versions to those used in Colab.

## Selected dataset

RiceyLeafDisease, version 1 (27 December 2023).

- Source: https://data.mendeley.com/datasets/t46kkgh2yw/1
- DOI: https://doi.org/10.17632/t46kkgh2yw.1
- Authors: Mehedi Hasan, Sonia Khatun, Md. Abu Raihan, Abdul Hasib Uddin.
- License: CC BY 4.0, https://creativecommons.org/licenses/by/4.0/
- Publisher reports 1,701 original images and 5,188 additional augmented images across eight categories, collected in Bangladesh.

## Initial model scope

- Healthy rice leaf
- Leaf blast
- Brown spot
- Bacterial leaf blight

## Obtain and prepare images

1. Open the source page and select Download All.
2. Save the downloaded archive in `data/raw/` and preserve it unchanged.
3. Inspect the archive's folder structure and identify original images separately from augmented images. Do not infer which are original without checking the supplied files.
4. Review labels and remove duplicates before splitting. Keep images from the same plant or capture session together where metadata permits.
5. Split original images into training, validation, and test sets. Apply augmentation only to training images; never distribute variants of the same image across splits.
6. Record per-class counts and evaluate per-class precision, recall, and a confusion matrix. Independently collected Philippine rice photos are needed to evaluate local performance.

The supplied `data/raw/` collection contains 1,701 images across eight folders, matching the publisher's original-image count. A baseline was trained separately in Colab; the user reported 106/132 correct test predictions (80.30%). Model artifacts have not been inspected locally.

Run `python scripts/prepare_dataset.py` to create a reproducible, provisional four-class split in `data/processed/manifest.csv`, with an audit report in `data/processed/report.json`. Source images are never changed. The manifest references source paths rather than copying images.

The first preparation run retained 863 unique images: 603 training, 128 validation, and 132 test. It excluded 44 exact duplicate copies and one conflicting-label group (two identical files labeled bacterial leaf blight and leaf blast). Those exclusions are recorded in the report. Near duplicates, image decoding, and expert label validation remain unchecked. Plant/session metadata is unavailable, so the image-level split must not be treated as an independent farm evaluation.

## Treatment guidance

Image labels do not provide treatment recommendations. Maintain a separate expert-reviewed knowledge base with Philippine agricultural references and applicable current product labels. Do not generate pesticide dosages from model predictions.

`scripts/colab_guidance.py` can be pasted into Colab after the photo prediction cell. It maps the existing `scores` and `class_names` to general management information, source links, and model limitations. Its disease information is paraphrased from IRRI-linked Rice Doctor factsheets hosted by Lucidcentral, accessed 5 November 2026. This is draft educational guidance, pending Philippine specialist review; pesticide products and dosages are intentionally not specified because none have been verified for local use. No score cutoff has been validated to detect unsupported conditions.

## Attribution

Hasan, Mehedi; Khatun, Sonia; Raihan, Md. Abu; Uddin, Abdul Hasib (2023), “RiceyLeafDisease: An Extensive Image Dataset of Diverse Rice Leaf Diseases from Different Regions of Bangladesh.”, Mendeley Data, V1, doi: 10.17632/t46kkgh2yw.1.

Document any filtering, relabeling, resizing, or augmentation when derived data is created.
