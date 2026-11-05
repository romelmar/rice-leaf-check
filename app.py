"""Local rice leaf classification app. Run: python -m streamlit run app.py"""
import hashlib
import io
import json
import tempfile
from pathlib import Path

import numpy as np
import streamlit as st
import tensorflow as tf
from PIL import Image, ImageOps, UnidentifiedImageError

from scripts.colab_guidance import GUIDANCE

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='Rice Leaf Check', page_icon='🌾', layout='wide')


@st.cache_resource
def load_model(model_bytes):
    # Keras expects a filename. The temporary file is removed after loading.
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'rice_baseline.keras'
        path.write_bytes(model_bytes)
        network = tf.keras.models.load_model(str(path), compile=False, safe_mode=True)
    if network.input_shape != (None, 224, 224, 3) or network.output_shape != (None, 4):
        raise ValueError('Expected the saved 224 × 224 rice model with four outputs.')
    return network


st.image(str(ROOT / 'assets/scabcs-logo.png'), width=280, alt='SCABCS logo with rice stalk and leaves')
st.caption('RICE LEAF CHECK · RESEARCH PROTOTYPE')
st.title('A closer look at your rice leaves')
st.write('Upload a clear leaf photo to explore a possible disease and practical management information.')
st.info('Supports healthy rice, leaf blast, bacterial leaf blight, and brown spot. Other conditions can receive one of these labels. A model score is not a confirmed diagnosis.')

with st.sidebar:
    st.header('Your trained model')
    st.write('Download these two files from Google Drive → rice-project → models, then select them below. Use only your own trusted model file.')
    uploaded_model = st.file_uploader('rice_baseline.keras', type=['keras'])
    uploaded_names = st.file_uploader('class_names.json', type=['json'])
    st.caption('Alternatively, place both files in this project’s models folder.')
    st.divider()
    st.caption('Baseline: 106/132 test photos correct (80.30%), reported from Colab. Local farm performance has not been established.')

local_model = ROOT / 'models/rice_baseline.keras'
local_names = ROOT / 'models/class_names.json'
# Use a complete uploaded pair or a complete local pair; never mix artifacts.
if uploaded_model is not None and uploaded_names is not None:
    model_bytes, names_bytes = uploaded_model.getvalue(), uploaded_names.getvalue()
elif uploaded_model is not None or uploaded_names is not None:
    st.warning('Select both model files in the sidebar to continue.')
    st.stop()
elif local_model.is_file() and local_names.is_file():
    model_bytes, names_bytes = local_model.read_bytes(), local_names.read_bytes()
else:
    st.warning('First, select your two saved model files in the sidebar.')
    st.stop()

try:
    names = json.loads(names_bytes)
    if (not isinstance(names, list) or len(names) != 4
            or not all(isinstance(name, str) for name in names)
            or set(names) != set(GUIDANCE)):
        raise ValueError('Category names must match the four trained rice categories.')
    with st.spinner('Loading your model…'):
        network = load_model(model_bytes)
except Exception as error:
    st.error(f'Could not load the model files: {error}')
    st.caption('If this is a version compatibility error, use the TensorFlow/Keras versions from your Colab notebook.')
    st.stop()

st.success('Your model is ready.')
results_column, photo_column = st.columns([3, 2], gap='large')
photo = photo_column.file_uploader('Choose a rice leaf photo', type=['jpg', 'jpeg', 'png'])
if photo is None:
    photo_column.caption('Use a sharp close-up in natural light. Include the affected area of the leaf.')
    results_column.info('Choose a photo on the right to check your rice leaf.')
    st.stop()

try:
    if photo.size > 10 * 1024 * 1024:
        raise ValueError('Choose a photo smaller than 10 MB.')
    with Image.open(io.BytesIO(photo.getvalue())) as source:
        if source.width * source.height > 25_000_000:
            raise ValueError('Choose a photo smaller than 25 megapixels.')
        image = ImageOps.exif_transpose(source).convert('RGB')
except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as error:
    photo_column.error(f'Unable to open this photo: {error}')
    st.stop()

photo_column.image(image, caption='Your uploaded leaf photo', width='stretch')
signature = hashlib.sha256(photo.getvalue() + model_bytes + names_bytes).hexdigest()
if photo_column.button('Check leaf', type='primary'):
    st.session_state.pop('result', None)
    try:
        with st.spinner('Examining the leaf…'):
            batch = np.asarray(image.resize((224, 224)), dtype=np.float32)[None, ...]
            # Input preprocessing is already part of the trained model.
            scores = np.asarray(network.predict(batch, verbose=0))[0]
            if (scores.shape != (4,) or not np.isfinite(scores).all()
                    or (scores < 0).any() or (scores > 1).any()
                    or not np.isclose(scores.sum(), 1, atol=.01)):
                raise ValueError('The model did not return four valid category probabilities.')
            st.session_state.result = (signature, scores.tolist())
    except Exception as error:
        st.error(f'Prediction failed: {error}')

with results_column:
    result = st.session_state.get('result')
    if result and result[0] == signature:
        scores = np.asarray(result[1])
        index = int(scores.argmax())
        info = GUIDANCE[names[index]]
        st.subheader('Model-selected category: ' + info['name'])
        st.metric('Model score', f'{scores[index]:.1%}')
        st.caption('This score is not a verified probability of diagnosis. The model cannot reliably reject unsupported conditions.')
        with st.expander('Compare all category scores'):
            for i in np.argsort(scores)[::-1]:
                st.write(f"{GUIDANCE[names[i]]['name']} — {scores[i]:.1%}")
                st.progress(float(scores[i]))
        st.subheader('Symptoms to compare')
        st.write(info['symptoms'])
        st.subheader('Management guidance')
        for step in info['management']:
            st.write('• ' + step)
        if info['source']:
            st.link_button('Read the disease factsheet', info['source'])
        st.warning('General information pending Philippine specialist review. Confirm the disease before treatment. Pesticide products and dosages have not been verified for local use.')
        st.download_button('Download this result', json.dumps({
            'category': names[index], 'scores': dict(zip(names, scores.tolist())),
            'guidance': info, 'notice': 'Model prediction only; confirm before treatment.'
        }, indent=2), file_name='rice-leaf-result.json', mime='application/json')
