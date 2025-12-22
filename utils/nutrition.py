# Used for nutrition calculations


# Basal Metabolic Rate (BMR) calculation
def bmr_calculation(weight_kg, height_cm, age, sex):
    # Mifflin-st Jeor Equation
    if sex == 'male':
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

# Total Daily Energy Expenditure (TDEE) calculation
def tdee_calculation(bmr, activity_level='sedentary'):
    factors = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9
    }
    factor = factors.get(activity_level, 1.2)
    return bmr * factor

def goal_category_calculation(percent):
    if percent < 0:
        return 'cut'
    elif percent == 0:
        return 'maintain'
    else:
        return 'bulk'

def tdee_adjustment_calculation(tdee, percent):
    if percent < -25:
        percent = -25
    elif percent > 25:
        percent = 25

    adjusted_calories = tdee * (1 + percent / 100)
    goal_category = goal_category_calculation(percent)
    return adjusted_calories, goal_category

def macros_calculation(weight_kg, calories):
    protein = weight_kg * 2
    fat = weight_kg * 1

    calories_from_protein = protein * 4
    calories_from_fat = fat * 9
    calories_remaining = calories - (calories_from_protein + calories_from_fat)
    carbs = max(calories_remaining / 4, 0)

    return{
        'calories': calories,
        'protein': protein,
        'fat': fat,
        'carbs': carbs
    }