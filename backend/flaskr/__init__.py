import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from sqlalchemy.sql.elements import Null

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  CORS(app, resources={'/': {'origins': '*'}})

  @app.after_request
  def after_request(response):
      response.headers.add(
          "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
      )
      response.headers.add(
          "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
      )
      return response
      
  '''
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def retrieve_categories():
      categories = Category.query.all()
      categories_dict = {}
      for category in categories:
          categories_dict[category.id] = category.type
      if len(categories) == 0:
          abort(404)

      return jsonify(
          {
              "success": True,
              "categories": categories_dict,
          }
      )

  '''
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  '''
  def paginate_questions(request, selection):
      page = request.args.get("page", 1, type=int)
      start = (page - 1) * QUESTIONS_PER_PAGE
      end = start + QUESTIONS_PER_PAGE

      questions = [question.format() for question in selection]
      current_questions = questions[start:end]

      return current_questions

  @app.route("/questions")
  def retrieve_questions():
      selection = Question.query.all()
      current_questions = paginate_questions(request, selection)
      categories = Category.query.all()
      categories_dict = {}
      for category in categories:
          categories_dict[category.id] = category.type
          
      if len(current_questions) == 0:
          abort(404)

      return jsonify(
          {
              "success": True,
              "questions": current_questions,
              "total_questions": len(selection),
              "categories": categories_dict
              
          }
      )

  '''
  Create an endpoint to DELETE question using a question ID. 
  '''
  @app.route("/questions/<int:question_id>", methods=["DELETE"])
  def delete_question(question_id):
      try:
          question = Question.query.filter(Question.id == question_id).one_or_none()

          if question is None:
              abort(404)

          question.delete()
          selection = Question.query.all()
          current_questions = paginate_questions(request, selection)

          return jsonify(
              {
                  "success": True,
                  "deleted": question_id,
                  "questions": current_questions,
                  "total_questions": len(selection)
              }
          )

      except:
            abort(422)
            
  '''
  Create an endpoint to POST a new question
  '''
  @app.route("/questions", methods=["POST"])
  def create_question():
      body = request.get_json()

      new_question = body.get("question", None)
      new_answer = body.get("answer", None)
      new_category = body.get("category", None)
      new_difficulty = body.get("difficulty", None)
      search = body.get("search", None)

      try:
          if search:
              selection = Question.query.filter(
                  Question.question.ilike("%{}%".format(search))
              )
              current_questions = paginate_questions(request, selection)

              return jsonify(
                  {
                      "success": True,
                      "questions": current_questions,
                      "total_questions": len(Question.query.all()),
                  }
              )

          else:
              if ((new_question is None) or (new_answer is None)
                    or (new_difficulty is None) or (new_category is None)):
                abort(422)

              question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
              question.insert()

              selection = Question.query.order_by(Question.id).all()
              current_questions = paginate_questions(request, selection)

              return jsonify(
                  {
                      "success": True,
                      "created": question.id,
                      "questions": current_questions,
                      "total_questions": len(selection)
                  }
              )

      except:
          abort(422)


  '''
  Create a POST endpoint to get questions based on a search term. 
  '''
  @app.route("/questions/search", methods=["POST"])
  def search_questions():
        body = request.get_json()
        search = body.get("searchTerm", None)

        try:
            if search:
                selection = Question.query.filter(Question.question.ilike
                                                  (f"%{search}%")).all()

            paginated = paginate_questions(request, selection)

            return jsonify({
                "success": True,
                "questions":  paginated,
                "total_questions": len(selection)
                
            })
        except:
            abort(404)
  '''
  Create a GET endpoint to get questions based on category. 
  '''
  @app.route("/categories/<int:category_id>/questions", methods=["GET"])
  def retrieve_questions_by_category(category_id):
      try:
        
        questions = Question.query.filter(Question.category == str(category_id)).all()

        return jsonify({
            "success": True,
            "questions": [question.format() for question in questions],
            "total_questions": len(questions),
            "current_category": category_id
        })
      except:
          abort(400)


  '''
  Create a POST endpoint to get questions to play the quiz. 
  '''
  @app.route("/quizzes", methods=["POST"])
  def play_quiz():
        body = request.get_json()
        previous_questions = body.get("previous_questions", None)
        category = body.get("quiz_category", None)
        if((category == None) or (previous_questions == None)):
            abort(422)
        
        if category['id'] == 0:
            quiz = Question.query.all()
        else:
            quiz = Question.query.filter_by(category=category['id']).all()
        
        def random_question():
            return random.choice(quiz).format()
        
        new_question = random_question()

        def if_used(new_question):
            if(new_question in previous_questions):
                return True
            else:
                return False
        while(if_used(new_question)):
            new_question = random_question()
            
            if(len(previous_questions) == len(quiz)):
                return jsonify({
                'success': True,
                })
        
        return jsonify({
            "success": True,
            "question": new_question
        })


  '''
  Create error handlers for all expected errors 
  '''
  @app.errorhandler(404)
  def not_found(error):
      return jsonify({
          "success": False,
          "error": 404,
          "message": "resource not found"
      }), 404

  @app.errorhandler(422)
  def unprocessable(error):
      return jsonify({
          "success": False,
          "error": 422,
          "message": "unprocessable"
      }), 422

  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
          "success": False,
          "error": 400,
          "message": "bad request"
      }), 400

  
  return app

    