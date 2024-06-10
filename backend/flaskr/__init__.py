from json import load
import os
import string
from unicodedata import category
from unittest import result
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from sqlalchemy.orm import load_only

from sqlalchemy import select

from models import setup_db, Question, Category, db
import traceback


QUESTIONS_PER_PAGE = 10

##Define pagination for the questions

def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    questions_for_curpage = questions[start:end]
    return questions_for_curpage


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    #### important revision!!!
    app.app_context().push()

    if test_config is None:
        setup_db(app)
    else:
        database_path = test_config.get('SQLALCHEMY_DATABASE_URI')
        setup_db(app, database_path=database_path)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route("/categories",methods=['GET'])
    def show_categories():
        categories = Category.query.all()
        
        if not categories: 
            abort(404)
        else:
            categorie_list = {v.id: v.type.lower() for v in categories}
        

        return jsonify({
            'success': True,
            'categories': categorie_list
        })



    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    
    @app.route('/questions',methods=['GET'])
    def show_questions():
        try:
            categories = Category.query.all()
            if not categories:
                abort(404)
            else:
                #categories_list = {v.id: v.type.lower() for v in categories}
                categories_list = {v.id: v.type for v in categories}
            
            selection = Question.query.order_by(Question.id).all()
            question_ct = len(selection)

            # get questions for current page
            questions_curpage = paginate_questions(request, selection)

            # if no questions
            if not questions_curpage: 
                abort(404)
            else:
                return jsonify({
                    'success': True,
                    'categories': categories_list,
                    'questions': questions_curpage,
                    'total_questions': question_ct
                    
                })
        except:
            print(Exception)
            abort(404)

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_question(id):
        try:
            question = Question.query.filter_by(id=id).one_or_none()
            ## if the question is not found
            if not question: 
                abort(422)
            else:
                question.delete()
                selection = Question.query.order_by(Question.id).all()
                questions_curpage = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'question_deleted_id':id,
                    'questions': questions_curpage,
                    'total_questions': len(selection)    
                    })

        except:
            print(Exception)
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    
    @app.route("/questions", methods=['POST'])
    def create_question():
        body = request.get_json()

        ## get information of new question
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)
        
        
        if not new_question or not new_answer:
            print('part of the new question form is empty')
            abort(422)
        else:
            try:
                question = Question(question=new_question, 
                                    answer=new_answer,
                                    category=new_category, 
                                    difficulty=new_difficulty)
                question.insert()

                selection = Question.query.order_by(Question.id).all()
                questions_curpage = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'created': question.id,
                    'questions': questions_curpage,
                    'total_questions': len(selection)
                })

            except:
                print(Exception)
                abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions/search', methods=['POST'])

    def search():
        body = request.get_json()
        search = body.get('searchTerm')
        questions = Question.query.filter(Question.question.ilike('%'+search+'%')).all()

        if not questions:
            abort(404)
        else:
            questions_curpage = paginate_questions(request, questions)
            return jsonify({
                'success': True,
                'questions': questions_curpage,
                'total_questions': len(questions),
                'currentCategory': '--'
            })
            

    

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    
    @app.route('/categories/<int:category_id>/questions',methods=['GET'])
    def category_questions(category_id):
        categories = Category.query.all()
        #print(categories)
 
        ## if category_id not in category 
        ## (based on category_id is continuous and it is the primary_key and it starts from 1)
        if category_id > len(categories):
            abort(404)
        else:
            try:
                selection = Question.query.filter(category_id == Question.category).all()
                questions_curpage = paginate_questions(request, selection)
    
                return jsonify({
                        "success": True,
                        "current_category": [v.type for v in categories if v.id == category_id ],
                        "questions": list(questions_curpage),
                        "total_questions": len(selection)
                        })
            except:
                print(Exception)
                abort(404)

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def quiz():
        body = request.get_json()
        ## get quiz category
        quiz_category = body.get('quiz_category')
        ## get previous question
        previous_question = body.get('previous_questions')

        try:
            ## if quiz for all category
            if (quiz_category['id'] == 0):
                questions_quiz = Question.query.filter(Question.id.notin_(previous_question)).all()
                print("debugging sarah:{} ".format(questions_quiz))
            else:
                questions_quiz = Question.query.filter(Question.id.notin_(previous_question), 
                Question.category == quiz_category['id']).all()
                print("debugging sarah:{} ".format(questions_quiz))

            next_question = None
            if(questions_quiz):
                next_question = random.choice(questions_quiz)
                questionfile = jsonify({
                    'success': True,
                    'question': {
                        "question": next_question.question,
                        "id": next_question.id,
                        "answer": next_question.answer,
                        "difficulty": next_question.difficulty,
                        "category": next_question.category                            
                        },
                    'previousQuestion': previous_question
                     })
                print("debugging sarah:{} ".format(next_question))
                return questionfile
            else:
                # if number of question < 5, end the quiz
                print("debugging sarah:{} ".format("forceEnd"))
                return jsonify({
                    'forceEnd': True})
        except:
            print(Exception)
            abort(404)



    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    
    ############# Error handlers #############

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            'error': 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(404)
    def page_not_found(error):
        return jsonify({
            "success": False,
            'error': 404,
            "message": "Page not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable_recource(error):
        return jsonify({
            "success": False,
            'error': 422,
            "message": "Unprocessable Content"
        }), 422
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            'error': 500,
            "message": "Internal server error"
        }), 500

    @app.errorhandler(405)
    def invalid_method(error):
        return jsonify({
            "success": False,
            'error': 405,
            "message": "Invalid method!"
        }), 405


    return app

  