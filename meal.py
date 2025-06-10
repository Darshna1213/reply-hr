import streamlit as st
import json
import requests # Used for making HTTP requests to the Gemini API

# API Key - Leave as empty string. The Canvas environment will provide it at runtime.
API_KEY = ""

# Function to call the Gemini API
async def generate_meal_plan(preferences, goals, num_meals_per_day):
    """
    Calls the Gemini API to generate a meal plan and shopping list.

    Args:
        preferences (str): Dietary preferences (e.g., vegan, keto, gluten-free).
        goals (str): Health goals (e.g., weight loss, muscle gain, maintenance).
        num_meals_per_day (int): Number of meals to generate per day.

    Returns:
        dict or None: Parsed JSON meal plan and shopping list, or None if an error occurs.
    """
    prompt = f"""
    Create a detailed 7-day weekly meal plan, including breakfast, lunch, and dinner (if {num_meals_per_day} is 3). Adjust meals based on the specified number of meals per day.
    For each meal, include a recipe name, a list of ingredients, and cooking instructions.
    Finally, provide a consolidated shopping list for the entire week's meal plan.

    Dietary Preferences: {preferences}
    Goals: {goals}
    Number of meals per day: {num_meals_per_day}

    The output MUST be in JSON format, adhering strictly to the following structure.
    Ensure all ingredients mentioned in recipes are included in the shopping_list.
    Provide realistic, diverse, and well-balanced meals.
    """

    # Define the JSON schema for the desired output
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "weekly_meal_plan": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "day": { "type": "STRING" },
                        "meals": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "type": { "type": "STRING" },
                                    "recipe_name": { "type": "STRING" },
                                    "ingredients": {
                                        "type": "ARRAY",
                                        "items": { "type": "STRING" }
                                    },
                                    "instructions": { "type": "STRING" }
                                },
                                "required": ["type", "recipe_name", "ingredients", "instructions"]
                            }
                        }
                    },
                    "required": ["day", "meals"]
                }
            },
            "shopping_list": {
                "type": "ARRAY",
                "items": { "type": "STRING" }
            }
        },
        "required": ["weekly_meal_plan", "shopping_list"]
    }

    headers = {
        'Content-Type': 'application/json'
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
    }

    # Construct the API URL
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

    try:
        # Make the API call
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        result = response.json()

        # Check if the response contains the expected structure
        if result and result.get('candidates') and result['candidates'][0].get('content') and \
           result['candidates'][0]['content'].get('parts') and result['candidates'][0]['content']['parts'][0].get('text'):
            
            json_string = result['candidates'][0]['content']['parts'][0]['text']
            # Parse the text content as JSON
            parsed_json = json.loads(json_string)
            return parsed_json
        else:
            st.error("Error: Unexpected response format from Gemini API.")
            st.json(result) # Display the raw response for debugging
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to Gemini API: {e}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Error parsing JSON response from Gemini API: {e}")
        st.write("Raw API response content (might be malformed JSON):")
        st.code(response.text) # Show the problematic raw text
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

# --- Streamlit UI ---
st.set_page_config(page_title="🍽️ AI Meal Plan Generator", layout="wide")

st.title("🍽️ AI Weekly Meal Plan Generator")
st.markdown("Enter your dietary preferences and health goals to get a personalized weekly meal plan and shopping list!")

with st.sidebar:
    st.header("Your Preferences")
    dietary_preferences = st.text_area(
        "Dietary Preferences (e.g., Vegan, Keto, Gluten-Free, allergies like peanuts)",
        "Vegetarian, no dairy, low carb"
    )
    health_goals = st.selectbox(
        "Health Goals",
        ["Weight Loss", "Muscle Gain", "Maintenance", "General Healthy Eating"],
        index=0
    )
    num_meals = st.slider(
        "Meals per day",
        min_value=1,
        max_value=3,
        value=3,
        help="Number of main meals (e.g., 3 for Breakfast, Lunch, Dinner)"
    )

    generate_button = st.button("Generate Meal Plan", type="primary")

st.markdown("---")

if generate_button:
    if not dietary_preferences:
        st.warning("Please enter your dietary preferences.")
    else:
        st.info("Generating your personalized meal plan... This might take a moment!")
        
        # Use st.spinner for a loading indicator
        with st.spinner('Crafting your delicious weekly plan...'):
            import asyncio
            meal_plan_data = asyncio.run(generate_meal_plan(dietary_preferences, health_goals, num_meals))

        if meal_plan_data:
            st.success("Meal Plan Generated Successfully!")

            # Display Weekly Meal Plan
            st.header("Weekly Meal Plan 🗓️")
            tab_titles = [day_data['day'] for day_data in meal_plan_data['weekly_meal_plan']]
            tabs = st.tabs(tab_titles)

            for i, day_data in enumerate(meal_plan_data['weekly_meal_plan']):
                with tabs[i]:
                    st.subheader(f"___{day_data['day']}___")
                    if day_data['meals']:
                        for meal in day_data['meals']:
                            st.markdown(f"**{meal['type']}:** {meal['recipe_name']}")
                            st.markdown("**Ingredients:**")
                            for ingredient in meal['ingredients']:
                                st.write(f"- {ingredient}")
                            st.markdown("**Instructions:**")
                            st.markdown(meal['instructions'])
                            st.markdown("---")
                    else:
                        st.write("No meals planned for this day.")

            # Display Shopping List
            st.header("Shopping List 🛒")
            shopping_list = meal_plan_data.get('shopping_list', [])
            if shopping_list:
                cols = st.columns(3) # Display in 3 columns for better readability
                for idx, item in enumerate(shopping_list):
                    cols[idx % 3].checkbox(item, value=False, key=f"item_{idx}")
            else:
                st.write("No shopping list generated.")
