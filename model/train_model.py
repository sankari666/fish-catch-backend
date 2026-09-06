import os
import tensorflow as tf
from keras import layers, models

# ============================================================
# PATHS
# ============================================================

# Current folder:
# D:\React ja app\fishrepo\backend\model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Dataset:
# D:\React ja app\fishrepo\backend\model\fish_dataset
DATASET_PATH = os.path.join(BASE_DIR, "fish_dataset")

# Model:
# D:\React ja app\fishrepo\backend\model\fish_model.h5
MODEL_PATH = os.path.join(BASE_DIR, "fish_model.h5")

# Labels:
# D:\React ja app\fishrepo\backend\model\labels.txt
LABELS_PATH = os.path.join(BASE_DIR, "labels.txt")


# ============================================================
# TRAINING SETTINGS
# ============================================================

IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 10


# ============================================================
# CHECK DATASET
# ============================================================

print("========================================")
print("FISH MODEL TRAINING")
print("========================================")
print()

print("Dataset path:")
print(DATASET_PATH)
print()

if not os.path.exists(DATASET_PATH):
    print("ERROR: Dataset folder not found!")
    print(DATASET_PATH)
    raise FileNotFoundError(
        f"Dataset not found: {DATASET_PATH}"
    )

print("Dataset found successfully.")
print()


# ============================================================
# LOAD TRAINING DATA
# ============================================================

train_ds = tf.keras.preprocessing.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE
)


# ============================================================
# LOAD VALIDATION DATA
# ============================================================

val_ds = tf.keras.preprocessing.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE
)


# ============================================================
# GET CLASS NAMES
# ============================================================

class_names = train_ds.class_names

print()
print("========================================")
print("FISH CLASSES")
print("========================================")

for i, class_name in enumerate(class_names):
    print(f"{i}: {class_name}")

print()
print("Number of classes:", len(class_names))
print()


# ============================================================
# IMPROVE DATA PIPELINE
# ============================================================

AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.cache().shuffle(1000).prefetch(
    buffer_size=AUTOTUNE
)

val_ds = val_ds.cache().prefetch(
    buffer_size=AUTOTUNE
)


# ============================================================
# CREATE CNN MODEL
# ============================================================

model = models.Sequential([

    # Normalize pixel values
    layers.Rescaling(1.0 / 255),

    # First convolution block
    layers.Conv2D(
        32,
        3,
        activation="relu"
    ),
    layers.MaxPooling2D(),

    # Second convolution block
    layers.Conv2D(
        64,
        3,
        activation="relu"
    ),
    layers.MaxPooling2D(),

    # Third convolution block
    layers.Conv2D(
        128,
        3,
        activation="relu"
    ),
    layers.MaxPooling2D(),

    # Convert feature maps to vector
    layers.Flatten(),

    # Fully connected layer
    layers.Dense(
        128,
        activation="relu"
    ),

    # Output layer
    layers.Dense(
        len(class_names),
        activation="softmax"
    )
])


# ============================================================
# COMPILE MODEL
# ============================================================

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)


# ============================================================
# DISPLAY MODEL
# ============================================================

print("========================================")
print("MODEL ARCHITECTURE")
print("========================================")

model.summary()

print()


# ============================================================
# TRAIN MODEL
# ============================================================

print("========================================")
print("STARTING TRAINING")
print("========================================")
print()

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS
)


# ============================================================
# SAVE MODEL
# ============================================================

print()
print("========================================")
print("SAVING MODEL")
print("========================================")

model.save(MODEL_PATH)

print()
print("MODEL SAVED SUCCESSFULLY")
print("Model:", MODEL_PATH)


# ============================================================
# SAVE LABELS
# ============================================================

with open(LABELS_PATH, "w") as f:

    for label in class_names:
        f.write(label + "\n")


print("Labels:", LABELS_PATH)


# ============================================================
# FINAL INFORMATION
# ============================================================

print()
print("========================================")
print("TRAINING COMPLETED")
print("========================================")

print("Classes:", class_names)
print("Number of classes:", len(class_names))
print("Image size:", IMG_SIZE)
print("Batch size:", BATCH_SIZE)
print("Epochs:", EPOCHS)

print()
print("Files created:")
print(MODEL_PATH)
print(LABELS_PATH)

print()
print("========================================")
print("DONE")
print("========================================")