import requests

from flask import Flask, redirect, render_template, flash, g, session, request, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from flask_migrate import Migrate
from datetime import datetime
from models import connect_db, db, User, Recipe, User_Favorite, User_Comment
from forms import UserAddForm, UserEditForm, LoginForm
from sqlalchemy.exc import IntegrityError

CURR_USER_KEY = "curr_user"
API_URL = "https://api.spoonacular.com/"
API_KEY = '19906d120d454be7b19ae9cca4a92db5'


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///recipes-app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.config['SECRET_KEY'] = "123letsjam"

debug = DebugToolbarExtension(app)

connect_db(app)

migrate = Migrate(app,db)



####### Homepage & Login ###########

@app.route('/')
def homepage():
    """Show homepage:
    - anon users: Landing
    - logged in: Welcome screen + form + recipes list
    """
    
    if g.user:
  
        return render_template('home.html',
        user= g.user)

    else:
        return render_template('home.html')




############ USER LOGIN & LOGOUT #############

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/register/<int:id>', methods=["GET", "POST"])
def register_and_recipe(id):
    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('User/register.html', form=form)

        do_login(user)

        return redirect(f"/recipe/{id}")

    else:
        return render_template('User/register.html', form=form)

@app.route('/register', methods=["GET", "POST"])
def register():
    """Handle user signup.
    Create new user and add to DB. Redirect to home page.
    If form not valid, present form.
    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('User/register.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('User/register.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('User/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    if CURR_USER_KEY in session:
        session.pop(CURR_USER_KEY)
        flash("Successfully logged out!", category="danger")
        return redirect("/login")
    return redirect('/login')

@app.route('/users/edit', methods=["GET", "POST"])
def edit_user():
    """ edit user """
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = UserEditForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(id=g.user.id).first()

        # if user's password is correct , edit.
        if User.authenticate(user.username, form.password.data):
            try:
                
                user.username = form.username.data if form.username.data else user.username
                user.image_url = form.image_url.data if form.image_url.data else user.image_url
                
                db.session.add(user)
                db.session.commit()

                flash("Edited successfully!", 'success')
                return redirect('/users/profile')

            except IntegrityError:
                flash("E-mail already taken", 'danger')
                return render_template('User/edit.html', form=form, user=g.user)
        else:
            flash("Invalid Password", 'danger')
            return render_template('User/edit.html', form=form, user=g.user)
    else:
        return render_template('User/edit.html', form=form, user=g.user)

@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/login")

@app.route("/user/deleteprofile", methods=["GET"])
def show_delete_profile():
    """delete user profile"""

    if not g.user:
        flash("Access Denied Please Login First", "danger")
        return redirect("/login") 

    
    return render_template("User/deleteprofile.html")



@app.route("/user/deleteprofile", methods=["POST"])
def delete_profile():
    """delete user profile"""

    if not g.user:
        flash("Access Denied Please Login First", "danger")
        return redirect("/login") 

    db.session.delete(g.user)
    db.session.commit()
    do_logout()
    
    return redirect("/")


@app.route("/user/editprofile", methods=["GET", "POST"])
def edit_profile():
    """edit profile info"""

    if not g.user:
        flash("Access Denied Please Login First", "danger")
        return redirect("/login") 

    form = UserAddForm(obj=g.user)

    if form.validate_on_submit():
        
        g.user.username = form.username.data
        g.user.first_name = form.first_name.data
        g.user.last_name = form.last_name.data
        password = form.password.data

        user = User.authenticate(g.user.username, password)
        if user:

            db.session.add(g.user)
            db.session.commit()

            return redirect("/user")

        else:
            flash("Password Incorrect")
 
    return render_template("User/edit.html", form = form, user_id = g.user.id)


#################################################

@app.route("/", methods=["GET"])
def show_homepage():
    """show homepage"""
    
    return render_template("home.html")

@app.route("/searchbyingredients", methods=["GET"])
def show_search_by_ingredients():
    """show search by ingredients"""
    
    return render_template("searchbyingredients.html")

@app.route("/searchbyingredients", methods=["POST"])
def get_results_by_ingredients():
    """get results by ingredients"""
    ingredients = request.form["ingredients"]
 
    response = requests.get(f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={ingredients}&number=10&apiKey={API_KEY}&addRecipeInformation=true")
    results = response.json()



    if not len(results):
        no_results = "No recipes available with those ingredients, check your spelling"
    else:
        no_results = ""
    
    if g.user:
        if g.user.recipes:
            favorited_recipes = [recipe.recipe_id for recipe in g.user.recipes]
        else:
            favorited_recipes = None
    else:
        favorited_recipes = None
        
    return render_template("searchbyingredients.html", results = results ,  no_results= no_results, favorited_recipes = favorited_recipes)




@app.route("/", methods=["POST"])
def get_results():
    """show homepage"""
    dish = request.form["dish"]
    diet = request.form["diet"]
 
    response = requests.get(f"https://api.spoonacular.com/recipes/complexSearch?query={dish}&diet={diet}&addRecipeInformation=true&apiKey={API_KEY}")
    data = response.json()
  
    list = data["results"]
    results = [e for e in list]

    if not len(results):
        no_results = "No recipes available with that name, check your spelling"
    else:
        no_results = ""
    
    if g.user:
        if g.user.recipes:
            favorited_recipes = [recipe.recipe_id for recipe in g.user.recipes]
        else:
            favorited_recipes = None
    else:
        favorited_recipes = None
        
    return render_template("home.html", results = results, no_results= no_results, favorited_recipes = favorited_recipes)



@app.route("/dish/<int:dish_id>")
def show_dish(dish_id):
    """show recipe for specific dish"""
    response = requests.get(f"https://api.spoonacular.com/recipes/{dish_id}/information?&apiKey={API_KEY}")
    dish = response.json()
    
    print(dish)

    if dish["analyzedInstructions"]:
        for step in dish["analyzedInstructions"]:
            steps = [ e["step"] for e in step["steps"] ] 

    else:
        steps = []
    
    if g.user:
        if g.user.recipes:
            favorited_recipes = [recipe.recipe_id for recipe in g.user.recipes]
        else:
            favorited_recipes = None
    else: 
        favorited_recipes = None

    #comments  = User_Comment.query.filter(User_Comment.recipe_id == dish_id).order_by(
   # User_Comment.timestamp.desc()).all()

    return render_template("dish.html", dish = dish, steps = steps, favorited_recipes = favorited_recipes, comments = {})

@app.route("/dish/<int:dish_id>/grocerylist", methods=["POST"])
def send_grocery_list(dish_id):
    """ sends a grocery list email """
    if not g.user:
        flash("Access Denied Please Login First", "danger")
        return redirect("/login")

    response = requests.get(f"https://api.spoonacular.com/recipes/{dish_id}/information?&apiKey={API_KEY}")
    dish = response.json()

    if dish["analyzedInstructions"]:
        for step in dish["analyzedInstructions"]:
            steps = [ e["step"] for e in step["steps"] ] 

    else:
        steps = []

    return redirect(f"/dish/{dish_id}")


@app.route("/user")
def show_user_details():
    """show user details"""

    if not g.user:
        flash("Access Denied Please Login First", "danger")
        return redirect("/login")

    else:
        favorites = User_Favorite.query.filter(User_Favorite.user_id == g.user.id).order_by(
        User_Favorite.timestamp.desc()).all()
      
        ordered_recipe_ids = [ favorite.recipe_id for favorite in favorites]
  
        ordered_favorites = [Recipe.query.get(id) for id in ordered_recipe_ids]
      
        return render_template("User/details.html", favorites = ordered_favorites )


@app.route("/favorite/<int:dish_id>", methods=["POST"])
def add_favorite_dish(dish_id):
    """add favorite dish"""

    if not g.user:
        flash("Access Denied Please Login First", "danger")
        return redirect("/login")
        
        
    if not Recipe.query.get(dish_id):
        response = requests.get(f"https://api.spoonacular.com/recipes/{dish_id}/information?&apiKey={API_KEY}")
        dish = response.json()
        new_recipe = Recipe(recipe_id = dish_id, title = dish["title"], image= dish["image"])
        db.session.add(new_recipe)
        db.session.commit()
        
    timestamp = datetime.utcnow()
    new_favorite = User_Favorite(user_id = g.user.id, timestamp = timestamp, recipe_id = dish_id)
    db.session.add(new_favorite)
    db.session.commit()

    return jsonify(message="Dish Favorited")

@app.route("/removefavorite/<int:dish_id>", methods=["POST"])
def remove_favorite_dish(dish_id):
    """remove favorite dish"""

    if not g.user:
        flash("Access Denied Please Login First", "danger")
        return redirect("/login")

    favorite = User_Favorite.query.filter(
        User_Favorite.recipe_id == dish_id, User_Favorite.user_id == g.user.id).first()

    db.session.delete(favorite)
    db.session.commit()

    return jsonify(message="Removed Favorite")




@app.route("/dish/<int:dish_id>/comment", methods=["POST"])
def post_comment(dish_id):
    """post user comment"""
    if not g.user:
        flash("Access Denied Please Login First", "danger")
        return redirect("/login")

    comment = request.form["comment"]


    if not Recipe.query.get(dish_id):
        response = requests.get(f"https://api.spoonacular.com/recipes/{dish_id}/information?&apiKey={API_KEY}")
        dish = response.json()
        new_recipe = Recipe(recipe_id = dish_id, title = dish["title"], image= dish["image"])
        db.session.add(new_recipe)
        db.session.commit()
        
    timestamp = datetime.utcnow()
    new_comment = User_Comment(user_id = g.user.id, timestamp = timestamp, recipe_id = dish_id, comment = comment)
    db.session.add(new_comment)
    db.session.commit()
    
    return redirect(f"/dish/{dish_id}")


@app.route("/comment/<int:comment_id>/delete", methods=["POST"])
def delete_comment(comment_id):
    """delete users comment"""
    if not g.user:
        flash("Access Denied Please Login First", "danger")
        return redirect("/login")

    comment = User_Comment.query.get(comment_id)
    db.session.delete(comment)
    db.session.commit()

    return jsonify(message="comment deleted")


