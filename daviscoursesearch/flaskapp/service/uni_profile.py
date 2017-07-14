def classesTaughtByInstructor(instructor_id):
    # TODO map new instructor users to their profile; ask them to choose one if there are multiple options
    return []

def questionsForInstructorCourses(instructor_id):
    return []

def context(template_context):
    return {
        "classesTaught" : classesTaughtByInstructor(0),
        "questionsForClasses" : questionsForInstructorCourses(0),
    }
