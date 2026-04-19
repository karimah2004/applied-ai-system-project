import streamlit as st # type: ignore
from pawpal_system import Pet, Owner
from ai_advisor import answer_question
from rag_engine import list_supported_breeds, retrieve_chunks

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.markdown("""
<style>
    /* Page background */
    .stApp { background-color: #f9f5f0; }

    /* Main title */
    .pawpal-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #3d2b1f;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .pawpal-subtitle {
        text-align: center;
        color: #7a5c44;
        font-size: 1rem;
        margin-bottom: 1rem;
    }

    /* Section headers */
    h3 { color: #3d2b1f !important; }

    /* Buttons */
    .stButton > button {
        background-color: #c97b4b;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: background 0.2s;
    }
    .stButton > button:hover { background-color: #a85e32; color: white; }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background-color: #3d7a5c;
    }
    .stButton > button[kind="primary"]:hover { background-color: #2c5e44; }

    /* Info / success / warning boxes */
    .stAlert { border-radius: 10px; }

    /* Input fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border-color: #d4b99a;
    }

    /* Pet card */
    .pet-card {
        background: white;
        border-left: 5px solid #c97b4b;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }
    .pet-card h4 { color: #3d2b1f; margin: 0 0 0.2rem 0; font-size: 1.2rem; }
    .pet-card p  { color: #7a5c44; margin: 0; font-size: 0.9rem; }

    /* Advisor response box */
    .advisor-box {
        background: #eaf4ee;
        border-left: 5px solid #3d7a5c;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-top: 0.8rem;
    }

    /* Divider color */
    hr { border-color: #d4b99a; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="pawpal-title">🐾 PawPal+</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="pawpal-subtitle">AI-powered breed care assistant — '
    'answers grounded in real breed data</div>',
    unsafe_allow_html=True
)

# Initialize session state
if "owner" not in st.session_state:
    st.session_state.owner = None
if "current_pet" not in st.session_state:
    st.session_state.current_pet = None

st.divider()

# === OWNER SETUP ===
st.subheader("1️⃣ Owner Profile")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    available_time = st.number_input(
        "Available time today (minutes)",
        min_value=30, max_value=480, value=120
    )

if st.button("Create/Update Owner"):
    st.session_state.owner = Owner(
        name=owner_name,
        available_minutes=available_time,
        preferences={"priority_focus": "health_first"}
    )
    st.success(f"✓ Owner '{owner_name}' created!")

if st.session_state.owner:
    st.info(
        f"👤 **{st.session_state.owner.name}** | "
        f"{st.session_state.owner.available_minutes} min available | "
        f"{len(st.session_state.owner.pets)} pet(s)"
    )
else:
    st.warning("⚠️ Create an owner profile to continue")
    st.stop()

st.divider()

# === ADD PET ===
st.subheader("2️⃣ Add a Pet")

supported_breeds = list_supported_breeds()

col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
with col3:
    age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)

col1, col2 = st.columns(2)
with col1:
    breed_input = st.selectbox(
        "Breed",
        options=[""] + supported_breeds,
        format_func=lambda x: "Select a breed..." if x == "" else x,
    )
with col2:
    pet_notes = st.text_input("Notes", value="Energetic and friendly")

if st.button("Add Pet"):
    try:
        new_pet = Pet(
            name=pet_name,
            species=species,
            age_years=age,
            notes=f"{pet_notes} | Breed: {breed_input}" if breed_input else pet_notes
        )
        st.session_state.owner.add_pet(new_pet)
        st.session_state.current_pet = pet_name
        st.success(f"✓ Added {pet_name} the {species}!")
    except ValueError as e:
        st.error(f"Error: {e}")

if st.session_state.owner.pets:
    pet_names = [p.name for p in st.session_state.owner.pets]
    selected_pet = st.selectbox("Selected pet", pet_names)
    st.session_state.current_pet = selected_pet
else:
    st.info("No pets yet. Add your first pet above!")
    st.stop()

st.divider()

# === BREED ADVISOR ===
st.subheader("🧠 AI Breed Advisor")

pet = st.session_state.owner.get_pet(st.session_state.current_pet)
breed_for_qa = ""
if pet and pet.notes and "Breed:" in pet.notes:
    for part in pet.notes.split("|"):
        if "Breed:" in part:
            breed_for_qa = part.replace("Breed:", "").strip()

col1, col2 = st.columns([2, 3])
with col1:
    qa_breed = st.selectbox(
        "Breed to ask about",
        options=[""] + supported_breeds,
        index=([""] + supported_breeds).index(breed_for_qa) if breed_for_qa in supported_breeds else 0,
        format_func=lambda x: "Select a breed..." if x == "" else x,
        key="qa_breed"
    )
with col2:
    qa_question = st.text_input(
        "Your question",
        placeholder="How much exercise does my corgi need?"
    )

if st.button("Ask", type="primary"):
    if not qa_breed:
        st.warning("Please select a breed.")
    elif not qa_question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Looking up breed data..."):
            answer = answer_question(qa_breed, qa_question.strip())
        st.markdown(
            f'<div class="advisor-box">{answer}</div>',
            unsafe_allow_html=True
        )

st.divider()

# === PET SUMMARIES ===
st.subheader("🐾 Your Pets")

if not st.session_state.owner.pets:
    st.info("No pets added yet.")
else:
    for p in st.session_state.owner.pets:
        breed = ""
        notes_display = p.notes
        if p.notes and "Breed:" in p.notes:
            parts = p.notes.split("|")
            notes_display = parts[0].strip()
            for part in parts:
                if "Breed:" in part:
                    breed = part.replace("Breed:", "").strip()

        icon = "🐶" if p.species == "dog" else "🐱" if p.species == "cat" else "🐾"
        age_str = f"{p.age_years} yr{'s' if p.age_years != 1 else ''}"
        breed_tag = f" · {breed}" if breed else ""
        st.markdown(
            f'<div class="pet-card">'
            f'<h4>{icon} {p.name}</h4>'
            f'<p>{p.species.capitalize()} · {age_str}{breed_tag}</p>'
            f'{"<p>" + notes_display + "</p>" if notes_display else ""}'
            f'</div>',
            unsafe_allow_html=True
        )

        if breed:
            with st.expander(f"View {breed} care summary"):
                with st.spinner("Loading breed info..."):
                    chunks, canonical = retrieve_chunks(breed, "exercise diet grooming health age care")
                if chunks:
                    for chunk in chunks:
                        st.markdown(chunk)
                else:
                    st.info("No breed data available.")
