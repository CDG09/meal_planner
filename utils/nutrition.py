# Calculation functions for the nutrition macros within meals

# Calculates Basal Metabolic Rate (BMR) using the Mifflin-St Jeor equation

def calc_bmr(weight_kg, height_cm, age, sex):
    # use different equation depending on male or female
    if sex == 'male':
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

# Total Daily Energy Expenditure (TDEE) calculation based on Mifflin-St Jeor equation
def estimate_tdee(bmr, activity_level='sedentary'):
    activity_levels = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9
    }
    multiplier = activity_levels.get(activity_level, 1.2)
    return bmr * multiplier

# Determines the goal based on the % given by the user on the slider
def determine_goal(percent):
    if percent < 0:
        return 'cut'
    elif percent == 0:
        return 'maintain'
    else:
        return 'bulk'

def apply_goal_to_tdee(base_tdee, percent):
    # Creates a max and minimum percentage change for the goal
    if percent < -25:
        percent = -25
    elif percent > 25:
        percent = 25

    # Apply % change based on given activity level
    tdee = base_tdee * (1 + (percent / 100))
    activity_level = determine_goal(percent)

    return tdee, activity_level

def breakdown_macros(weight, total_calories):
    protein_g = weight * 2
    fat_g = weight * 1

    protein_calories = protein_g * 4
    fat_calories = fat_g * 9
    remaining_calories = total_calories - (protein_calories + fat_calories)
    carbs_g = remaining_calories / 4 if remaining_calories > 0 else 0

    return {
        'calories': round(total_calories),
        'protein_g': round(protein_g),
        'fat_g': round(fat_g),
        'carbs_g': round(carbs_g)
    }

