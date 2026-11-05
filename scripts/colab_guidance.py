"""Paste this entire file into a Colab cell after running photo prediction.

Requires scores and class_names from the prediction cell. General management
information only; not reviewed by a Philippine agricultural specialist.
"""
import numpy as np

SOURCE_BASE = (
    'https://keyserver.lucidcentral.org/key-server/data/'
    '0e090d01-0209-460e-810c-0d060708030c/media/Html/'
)

GUIDANCE = {
    'leaf_blast': {
        'name': 'Rice leaf blast',
        'symptoms': 'Elongated, pointed or spindle-shaped spots with pale centers and darker borders.',
        'management': [
            'Ask your local agriculture office to confirm the disease and assess crop stage and spread.',
            'Avoid excessive nitrogen; plan split applications with local agricultural advice.',
            'For future planting, select locally recommended blast-resistant varieties.',
        ],
        'source': SOURCE_BASE + 'Blast_%28Leaf_and_Collar%29.htm',
    },
    'bacterial_leaf_blight': {
        'name': 'Bacterial leaf blight',
        'symptoms': 'Yellowing and drying leaves; water-soaked or yellow-orange lesions progressing from tips or margins.',
        'management': [
            'Ask your local agriculture office to distinguish bacterial blight from similar diseases.',
            'Use balanced plant nutrition and avoid excessive nitrogen.',
            'Manage weed hosts and volunteer rice; arrange appropriate drainage with local advice.',
            'For future planting, choose locally recommended resistant varieties.',
        ],
        'source': SOURCE_BASE + 'Bacterial_blight.htm',
    },
    'brown_spot': {
        'name': 'Brown spot',
        'symptoms': 'Round to oval brown spots, sometimes with lighter centers and reddish-brown margins.',
        'management': [
            'Ask your local agriculture office to confirm the disease; symptoms can resemble blast.',
            'Check soil fertility and correct nutrient deficiencies using soil-test advice.',
            'For future planting, choose locally recommended resistant varieties.',
        ],
        'source': SOURCE_BASE + 'Brown_spot.htm',
    },
    'healthy': {
        'name': 'Healthy rice',
        'symptoms': 'The model selected healthy among its four supported categories.',
        'management': [
            'This prediction does not rule out other diseases, pests, or nutrient problems.',
            'Do not choose a disease treatment based on a healthy prediction.',
            'If symptoms are present or spreading, seek assessment from your local agriculture office.',
        ],
        'source': None,
    },
}


def show_guidance(scores, class_names):
    scores = np.asarray(scores, dtype=float)
    if scores.shape != (4,) or not np.isfinite(scores).all():
        raise ValueError('Expected four finite scores from one photo prediction.')
    if set(class_names) != set(GUIDANCE) or len(class_names) != 4:
        raise ValueError('Category names must match the four supported categories.')
    index = int(np.argmax(scores))
    info = GUIDANCE[class_names[index]]
    print('Model-selected category:', info['name'])
    print(f'Model score: {scores[index]:.1%} (not a verified probability of diagnosis)')
    print('Only four categories are supported; other conditions may receive one of these labels.')
    print('\nSymptoms to compare:', info['symptoms'])
    print('\nGeneral management information:')
    for step in info['management']:
        print('-', step)
    if info['source']:
        print('\nSource:', info['source'])
    print('\nPhilippine specialist review is pending. No pesticide product or dosage has been verified.')
    print('Before chemical treatment, confirm diagnosis and check current Philippine registration and the product label.')


if __name__ == '__main__':
    show_guidance(scores, class_names)
