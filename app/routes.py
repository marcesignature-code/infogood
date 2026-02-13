from flask import Blueprint, render_template, request
from slugify import slugify  # déjalo si ya lo usas en otras funciones
from .models import Listing


main = Blueprint("main", __name__)

@main.context_processor
def inject_slugify():
    return {'slugify': slugify}

@main.route("/")
def index():
    return render_template("pages/index.html")


@main.route("/home-splash/")
def home_splash():
    return render_template("pages/home-splash.html")


@main.route("/home-map/")
def home_map():
    return render_template("pages/home-map.html")


@main.route("/grid-layout-01/")
def grid_layout_01():
    listings = (
        Listing.query
        .filter_by(is_active=True)
        .order_by(Listing.sort_priority.desc(), Listing.created_at.desc())
        .all()
    )
    return render_template("pages/grid-layout-01.html", listings=listings)


@main.route("/grid-layout-02/")
def grid_layout_02():
    return render_template("pages/grid-layout-02.html")


@main.route("/list-layout-01/")
def list_layout_01():
    return render_template("pages/list-layout-01.html")


@main.route("/list-layout-02/")
def list_layout_02():
    return render_template("pages/list-layout-02.html")


@main.route("/half-map-01/")
def half_map_01():
    return render_template("pages/half-map-01.html")


@main.route("/half-map-05/")
def half_map_05():
    return render_template("pages/half-map-05.html")


@main.route("/single-listing-01/")
def listing_01_list_or_default():
    listings = [
        {
            'id' : 1,
            'img' : '/static/assets/img/single-1.jpg',
            'title' : 'Liman Restaurant',
            'reviews' : '42k Reviews',
        }
    ]
    listing = listings[0]
    return render_template("pages/single-listing-01.html", listing=listing)


@main.route("/single-listing-01/<string:title>/")
def single_listing_01(title):
    listings = [
        {
            'id' : 1,
            'img' : '/static/assets/img/list-1.jpg',
            'img1' : '/static/assets/img/team-1.jpg',
            'title' : 'The Big Bumbble Gym',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 4758',
            'miles' : '2.4 miles',
            'name' : 'Fitness',
            'icon' : 'fa-solid fa-dumbbell',
            'span' : 'catIcon cats-1',
            'plus' : '+2',
            'rating' : '4.5',
            'avarage' : 'good',
            'reviews' : '46 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 2,
            'img' : '/static/assets/img/list-2.jpg',
            'img1' : '/static/assets/img/team-2.jpg',
            'title' : 'Greenvally Real Estate',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 6150',
            'miles' : '3.7 miles',
            'name' : 'Real Estate',
            'icon' : 'bi bi-house-check',
            'span' : 'catIcon cats-2',
            'plus' : '+2',
            'rating' : '4.3',
            'avarage' : 'midium',
            'reviews' : '35 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 3,
            'img' : '/static/assets/img/list-3.jpg',
            'img1' : '/static/assets/img/team-3.jpg',
            'title' : 'Shree Wedding Planner',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 4785',
            'miles' : '2.7 miles',
            'name' : 'Weddings',
            'icon' : 'bi bi-lamp',
            'span' : 'catIcon cats-3',
            'plus' : '+1',
            'rating' : '4.8',
            'avarage' : 'excellent py-1 px-2 fw-semibold',
            'reviews' : '12 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 4,
            'img' : '/static/assets/img/list-4.jpg',
            'img1' : '/static/assets/img/team-4.jpg',
            'title' : 'The Blue Ley Light',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 6358',
            'miles' : '5.2 miles',
            'name' : 'Restaurant',
            'icon' : 'bi bi-cup-straw',
            'span' : 'catIcon cats-4',
            'plus' : '+1',
            'rating' : '4.6',
            'avarage' : 'good',
            'reviews' : '72 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 5,
            'img' : '/static/assets/img/list-5.jpg',
            'img1' : '/static/assets/img/team-5.jpg',
            'title' : 'Shreya Study Center',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 0210',
            'miles' : '3.8 miles',
            'name' : 'Education',
            'icon' : 'bi bi-mortarboard',
            'span' : 'catIcon cats-5',
            'plus' : '+1',
            'rating' : '4.2',
            'avarage' : 'midium',
            'reviews' : '112 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 6,
            'img' : '/static/assets/img/list-6.jpg',
            'img1' : '/static/assets/img/team-6.jpg',
            'title' : 'Mahroom Garage & Workshop',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 3251',
            'miles' : '2.4 miles',
            'name' : 'Showroom',
            'icon' : 'bi bi-backpack',
            'span' : 'catIcon cats-6',
            'plus' : '+1',
            'rating' : '4.9',
            'avarage' : 'excellent',
            'reviews' : '52 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 7,
            'img' : '/static/assets/img/list-9.jpg',
            'img1' : '/static/assets/img/team-7.jpg',
            'title' : 'The Great Dream Palace',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 5426',
            'miles' : '4.2 miles',
            'name' : 'Eat & Drink',
            'icon' : 'bi bi-cup-hot',
            'span' : 'catIcon cats-7',
            'plus' : '+2',
            'rating' : '4.9',
            'avarage' : 'excellent',
            'reviews' : '42 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 8,
            'img' : '/static/assets/img/list-8.jpg',
            'img1' : '/static/assets/img/team-8.jpg',
            'title' : 'Agroo Spa & Massage Center',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 2136',
            'miles' : '1.2 miles',
            'name' : 'Spa & Beauty',
            'icon' : 'bi bi-basket2',
            'span' : 'catIcon cats-8',
            'plus' : '+1',
            'rating' : '4.7',
            'avarage' : 'good',
            'reviews' : '76 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        }
    ]
    selected_listing = next((listing for listing in listings if slugify(listing['title']) == title), None)

    if selected_listing:
        return render_template('pages/single-listing-01.html', listing=selected_listing)
    else:
        return "listing not found", 404


@main.route("/single-listing-02/")
def listing_02_list_or_default():
    listings2 = [
        {
            'id' : 1,
            'img' : '/static/assets/img/single-2.jpg',
            'title' : 'Sangam Apartment',
            'location' : 'Old Paris, France',
        }
    ]
    listing2 = listings2[0]
    return render_template("pages/single-listing-02.html", listing2=listing2)


@main.route("/single-listing-02/<string:title>/")
def single_listing_02(title):
    listings2 = [
        {
            'id' : 1,
            'img' : '/static/assets/img/list-1.jpg',
            'img1' : '/static/assets/img/team-1.jpg',
            'title' : 'The Big Bumbble Gym',
            'number' : '+42 515 635 4758',
            'location' : 'Jakarta, USA',
            'name' : 'Health & Fitness',
            'icon' : 'fa-solid fa-dumbbell',
            'span' : 'catIcon cats-1',
            'reviews' : '42 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 2,
            'img' : '/static/assets/img/list-2.jpg',
            'img1' : '/static/assets/img/team-2.jpg',
            'title' : 'Greenvally Real Estate',
            'number' : '+42 515 635 6150',
            'location' : 'Jakarta, USA',
            'name' : 'Real Estate',
            'icon' : 'bi bi-house-check',
            'span' : 'catIcon cats-2',
            'reviews' : '39 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 3,
            'img' : '/static/assets/img/list-3.jpg',
            'img1' : '/static/assets/img/team-3.jpg',
            'title' : 'Shree Wedding Planner',
            'number' : '+42 515 635 4785',
            'location' : 'Jakarta, USA',
            'name' : 'Wedding & Evemts',
            'icon' : 'bi bi-lamp',
            'span' : 'catIcon cats-3',
            'reviews' : '65 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 4,
            'img' : '/static/assets/img/list-4.jpg',
            'img1' : '/static/assets/img/team-4.jpg',
            'title' : 'The Blue Ley Light',
            'number' : '+42 515 635 6358',
            'location' : 'Jakarta, USA',
            'name' : 'Restaurant',
            'icon' : 'bi bi-cup-straw',
            'span' : 'catIcon cats-4',
            'reviews' : '152 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 5,
            'img' : '/static/assets/img/list-5.jpg',
            'img1' : '/static/assets/img/team-5.jpg',
            'title' : 'Shreya Study Center',
            'number' : '+42 515 635 0210',
            'location' : 'Jakarta, USA',
            'name' : 'Education',
            'icon' : 'bi bi-mortarboard',
            'span' : 'catIcon cats-5',
            'reviews' : '72 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 6,
            'img' : '/static/assets/img/list-6.jpg',
            'img1' : '/static/assets/img/team-6.jpg',
            'title' : 'Mahroom Garage & Workshop',
            'number' : '+42 515 635 3251',
            'location' : 'Jakarta, USA',
            'name' : 'Showroom',
            'icon' : 'bi bi-backpack',
            'span' : 'catIcon cats-6',
            'reviews' : '42 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 7,
            'img' : '/static/assets/img/list-9.jpg',
            'img1' : '/static/assets/img/team-7.jpg',
            'title' : 'The Great Dream Palace',
            'number' : '+42 515 635 5426',
            'location' : 'Jakarta, USA',
            'name' : 'Eat & Drink',
            'icon' : 'bi bi-cup-hot',
            'span' : 'catIcon cats-7',
            'reviews' : '625 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 8,
            'img' : '/static/assets/img/list-8.jpg',
            'img1' : '/static/assets/img/team-8.jpg',
            'title' : 'Agroo Spa & Massage Center',
            'number' : '+42 515 635 2136',
            'location' : 'Jakarta, USA',
            'name' : 'Spa & Beauty',
            'icon' : 'bi bi-basket2',
            'span' : 'catIcon cats-8',
            'reviews' : '102 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 9,
            'img' : '/static/assets/img/list-12.jpg',
            'img1' : '/static/assets/img/team-1.jpg',
            'title' : 'Creative Wedding Planner',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 4758',
            'location' : 'Jakarta, USA',
            'miles' : '2.4 miles',
            'name' : 'Wedding',
            'icon' : 'fa-solid fa-dumbbell',
            'span' : 'catIcon cats-1',
            'plus' : '+2',
            'rating' : '4.5',
            'avarage' : 'good',
            'reviews' : '46 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        }
    ]
    selected_listing2 = next((listing2 for listing2 in listings2 if slugify(listing2['title']) == title), None)

    if selected_listing2:
        return render_template('pages/single-listing-02.html', listing2=selected_listing2)
    else:
        return "listing2 not found", 404


@main.route("/single-listing-03/")
def listing_03_list_or_default():
    listings3 = [
        {
            'id' : 1,
            'img' : '/static/assets/img/single-3.jpg',
            'title' : 'Groom Barber Shop',
            'location' : 'Old Paris, France',
        }
    ]
    listing3 = listings3[0]
    return render_template("pages/single-listing-03.html", listing3=listing3)


@main.route("/single-listing-03/<string:title>/")
def single_listing_03(title):
    listings3 = [
        {
            'id' : 1,
            'img' : '/static/assets/img/list-1.jpg',
            'img1' : '/static/assets/img/team-1.jpg',
            'title' : 'The Big Bumbble Gym',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 4758',
            'location' : 'Jakarta, USA',
            'name' : 'Fitness',
            'icon' : 'fa-solid fa-dumbbell',
            'span' : 'catIcon cats-1',
            'plus' : '+2',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 2,
            'img' : '/static/assets/img/list-2.jpg',
            'img1' : '/static/assets/img/team-2.jpg',
            'title' : 'Greenvally Real Estate',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 6150',
            'location' : 'Niwak, USA',
            'name' : 'Real Estate',
            'icon' : 'bi bi-house-check',
            'span' : 'catIcon cats-2',
            'plus' : '+2',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 3,
            'img' : '/static/assets/img/list-3.jpg',
            'img1' : '/static/assets/img/team-3.jpg',
            'title' : 'Shree Wedding Planner',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 4785',
            'location' : 'Jakarta, USA',
            'name' : 'Weddings',
            'icon' : 'bi bi-lamp',
            'span' : 'catIcon cats-3',
            'plus' : '+1',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 4,
            'img' : '/static/assets/img/list-4.jpg',
            'img1' : '/static/assets/img/team-4.jpg',
            'title' : 'The Blue Ley Light',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 6358',
            'location' : 'Chicago, USA',
            'name' : 'Restaurant',
            'icon' : 'bi bi-cup-straw',
            'span' : 'catIcon cats-4',
            'plus' : '+1',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 5,
            'img' : '/static/assets/img/list-5.jpg',
            'img1' : '/static/assets/img/team-5.jpg',
            'title' : 'Shreya Study Center',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 0210',
            'location' : 'Jakarta, USA',
            'name' : 'Education',
            'icon' : 'bi bi-mortarboard',
            'span' : 'catIcon cats-5',
            'plus' : '+1',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 6,
            'img' : '/static/assets/img/list-6.jpg',
            'img1' : '/static/assets/img/team-6.jpg',
            'title' : 'Mahroom Garage & Workshop',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 3251',
            'location' : 'New York, USA',
            'name' : 'Showroom',
            'icon' : 'bi bi-backpack',
            'span' : 'catIcon cats-6',
            'plus' : '+1',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 7,
            'img' : '/static/assets/img/list-9.jpg',
            'img1' : '/static/assets/img/team-7.jpg',
            'title' : 'The Great Dream Palace',
            'number' : '+42 515 635 5426',
            'location' : 'Jakarta, USA',
            'name' : 'Eat & Drink',
            'icon' : 'bi bi-cup-hot',
            'span' : 'catIcon cats-7',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 8,
            'img' : '/static/assets/img/list-8.jpg',
            'img1' : '/static/assets/img/team-8.jpg',
            'title' : 'Agroo Spa & Massage Center',
            'number' : '+42 515 635 2136',
            'location' : 'New York, USA',
            'name' : 'Spa & Beauty',
            'icon' : 'bi bi-basket2',
            'span' : 'catIcon cats-8',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 9,
            'img' : '/static/assets/img/list-12.jpg',
            'img1' : '/static/assets/img/team-1.jpg',
            'title' : 'Creative Wedding Planner',
            'number' : '+42 515 635 4758',
            'location' : 'Jakarta, USA',
            'name' : 'Wedding',
            'icon' : 'fa-solid fa-dumbbell',
            'span' : 'catIcon cats-1',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 10,
            'img' : '/static/assets/img/list-11.jpg',
            'img1' : '/static/assets/img/team-1.jpg',
            'title' : 'Cruzal Escort Services',
            'desc' : 'Cicero famously orated against his political.',
            'number' : '+42 515 635 0210',
            'location' : 'Jakarta, USA',
            'name' : 'Services',
            'icon' : 'fa-solid fa-dumbbell',
            'span' : 'catIcon cats-1',
            'plus' : '+2',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        }
    ]
    selected_listing3 = next((listing3 for listing3 in listings3 if slugify(listing3['title']) == title), None)

    if selected_listing3:
        return render_template('pages/single-listing-03.html', listing3=selected_listing3)
    else:
        return "listing3 not found", 404


@main.route("/single-listing-04/")
def listing_04_list_or_default():
    events = [
        {
            'id': 1,
            'img': '/static/assets/img/single-4.jpg',
            'title': 'Christmas Monday',
            'time': '10:30AM To 14:30PM',
        }
    ]
    event = events[0]
    return render_template("pages/single-listing-04.html", event=event)


@main.route("/single-listing-04/<string:title>/")
def single_listing_04(title):
    events = [
        {
            'id': 1,
            'img': '/static/assets/img/eve-1.jpg',
            'title': 'Learn Cooc with Shree Patel',
            'time': '10:30 AM To 02:40 PM',
            'name': 'Cooking',
            'color': 'badge badge-xs badge-danger',
            'date': '25',
            'month': 'Aug',
        },
        {
            'id': 2,
            'img': '/static/assets/img/eve-2.jpg',
            'title': 'Enjoy with Adobe Ceremoney',
            'time': '08:00 AM To 10:30 PM',
            'name': 'Nightlife',
            'color': 'badge badge-xs badge-success',
            'date': '15',
            'month': 'Sep',
        },
        {
            'id': 3,
            'img': '/static/assets/img/eve-3.jpg',
            'title': 'Join AI Community Workshop',
            'time': '8:30 AM To 12:20 PM',
            'name': 'Workshop',
            'color': 'badge badge-xs badge-warning',
            'date': '10',
            'month': 'Nov',
        }
    ]
    selected_event = next((event for event in events if slugify(event['title']) == title), None)

    if selected_event:
        return render_template('pages/single-listing-04.html', event=selected_event)
    else:
        return "event not found", 404


@main.route("/single-listing-05/")
def listing_05_list_or_default():
    listings5 = [
        {
            'id' : 1,
            'title' : 'TATA Nexon XM White',
        }
    ]
    listing5 = listings5[0]
    return render_template("pages/single-listing-05.html", listing5=listing5)


@main.route("/single-listing-05/<string:title>/")
def single_listing_05(title):
    listings5 = [
        {
            'id' : 1,
            'img' : '/static/assets/img/list-1.jpg',
            'img1' : '/static/assets/img/team-1.jpg',
            'title' : 'The Big Bumbble Gym',
            'number' : '+42 515 635 4758',
            'location' : 'Jakarta, USA',
            'name' : 'Health & Fitness',
            'icon' : 'fa-solid fa-dumbbell',
            'span' : 'catIcon cats-1',
            'reviews' : '42 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 2,
            'img' : '/static/assets/img/list-2.jpg',
            'img1' : '/static/assets/img/team-2.jpg',
            'title' : 'Greenvally Real Estate',
            'number' : '+42 515 635 6150',
            'location' : 'Jakarta, USA',
            'name' : 'Real Estate',
            'icon' : 'bi bi-house-check',
            'span' : 'catIcon cats-2',
            'reviews' : '39 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 3,
            'img' : '/static/assets/img/list-3.jpg',
            'img1' : '/static/assets/img/team-3.jpg',
            'title' : 'Shree Wedding Planner',
            'number' : '+42 515 635 4785',
            'location' : 'Jakarta, USA',
            'name' : 'Wedding & Evemts',
            'icon' : 'bi bi-lamp',
            'span' : 'catIcon cats-3',
            'reviews' : '65 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 4,
            'img' : '/static/assets/img/list-4.jpg',
            'img1' : '/static/assets/img/team-4.jpg',
            'title' : 'The Blue Ley Light',
            'number' : '+42 515 635 6358',
            'location' : 'Jakarta, USA',
            'name' : 'Restaurant',
            'icon' : 'bi bi-cup-straw',
            'span' : 'catIcon cats-4',
            'reviews' : '152 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 5,
            'img' : '/static/assets/img/list-5.jpg',
            'img1' : '/static/assets/img/team-5.jpg',
            'title' : 'Shreya Study Center',
            'number' : '+42 515 635 0210',
            'location' : 'Jakarta, USA',
            'name' : 'Education',
            'icon' : 'bi bi-mortarboard',
            'span' : 'catIcon cats-5',
            'reviews' : '72 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        },
        {
            'id' : 6,
            'img' : '/static/assets/img/list-6.jpg',
            'img1' : '/static/assets/img/team-6.jpg',
            'title' : 'Mahroom Garage & Workshop',
            'number' : '+42 515 635 3251',
            'location' : 'Jakarta, USA',
            'name' : 'Showroom',
            'icon' : 'bi bi-backpack',
            'span' : 'catIcon cats-6',
            'reviews' : '42 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 7,
            'img' : '/static/assets/img/list-9.jpg',
            'img1' : '/static/assets/img/team-7.jpg',
            'title' : 'The Great Dream Palace',
            'number' : '+42 515 635 5426',
            'location' : 'Jakarta, USA',
            'name' : 'Eat & Drink',
            'icon' : 'bi bi-cup-hot',
            'span' : 'catIcon cats-7',
            'reviews' : '625 Reviews',
            'btn' : 'Closed',
            'color' : 'listClose',
            'dollar' : '$$$',
            'btn1' : '',
            'tag' : 'false',
        },
        {
            'id' : 8,
            'img' : '/static/assets/img/list-8.jpg',
            'img1' : '/static/assets/img/team-8.jpg',
            'title' : 'Agroo Spa & Massage Center',
            'number' : '+42 515 635 2136',
            'location' : 'Jakarta, USA',
            'name' : 'Spa & Beauty',
            'icon' : 'bi bi-basket2',
            'span' : 'catIcon cats-8',
            'reviews' : '102 Reviews',
            'btn' : 'Open',
            'color' : 'listOpen',
            'dollar' : '$$$$',
            'btn1' : 'Featured',
            'tag' : 'true',
        }
    ]
    selected_listing5 = next((listing5 for listing5 in listings5 if slugify(listing5['title']) == title), None)

    if selected_listing5:
        return render_template('pages/single-listing-05.html', listing5=selected_listing5)
    else:
        return "listing5 not found", 404


@main.route("/dashboard-user/")
def dashboard_user():
    return render_template("pages/dashboard-user.html")


@main.route("/dashboard-my-profile/")
def dashboard_my_profile():
    return render_template("pages/dashboard-my-profile.html")


@main.route("/dashboard-my-bookings/")
def dashboard_my_bookings():
    return render_template("pages/dashboard-my-bookings.html")


@main.route("/dashboard-my-listings/")
def dashboard_my_listings():
    return render_template("pages/dashboard-my-listings.html")


@main.route("/dashboard-bookmarks/")
def dashboard_bookmarks():
    return render_template("pages/dashboard-bookmarks.html")


@main.route("/dashboard-messages/")
def dashboard_messages():
    return render_template("pages/dashboard-messages.html")


@main.route("/dashboard-reviews/")
def dashboard_reviews():
    return render_template("pages/dashboard-reviews.html")


@main.route("/dashboard-wallet/")
def dashboard_wallet():
    return render_template("pages/dashboard-wallet.html")


@main.route("/dashboard-add-listing/")
def dashboard_add_listing():
    return render_template("pages/dashboard-add-listing.html")


@main.route("/login/")
def login():
    return render_template("pages/login.html")


@main.route("/register/")
def register():
    return render_template("pages/register.html")


@main.route("/forgot-password/")
def forgot_password():
    return render_template("pages/forgot-password.html")


@main.route("/two-factor-auth/")
def two_factor_auth():
    return render_template("pages/two-factor-auth.html")


@main.route("/author-profile/")
def author_profile():
    return render_template("pages/author-profile.html")


@main.route("/booking-page/")
def booking_page():
    return render_template("pages/booking-page.html")


@main.route("/about-us/")
def about_us():
    return render_template("pages/about-us.html")


@main.route("/blog/")
def blog():
    return render_template("pages/blog.html")


@main.route("/blog-detail/")
def blog_list_or_default():
    blogs = [
        {
            'id' : 1,
            'img' : '/static/assets/img/gal-4.jpg',
            'title' : 'Top 10 Free Bootstrap Templates for Your Next Project',
            'date' : "6 Sep 2025",
        }
    ]
    blog = blogs[0]
    return render_template("pages/blog-detail.html", blog=blog)


@main.route("/blog-detail/<string:title>/")
def blog_detail(title):
    blogs = [
        {
            'id' : 1,
            'img' : '/static/assets/img/blog-2.jpg',
            'title' : '10 Must-Have Bootstrap Templates for Modern Web Design',
            'desc' : "Think of a news blog that's filled with content political against opponent Lucius Sergius.",
            'date' : "12 Feb 2025",
            'views' : "12k Views",
        },
        {
            'id' : 2,
            'img' : '/static/assets/img/blog-1.jpg',
            'title' : 'Top 5 Bootstrap Themes for E-commerce Websites.',
            'desc' : "Think of a news blog that's filled with content political against opponent Lucius Sergius.",
            'date' : "10 Jan 2025",
            'views' : "33k Views",
        },
        {
            'id' : 3,
            'img' : '/static/assets/img/blog-3.jpg',
            'title' : 'The Ultimate Guide to Customizing Bootstrap Templates',
            'desc' : "Think of a news blog that's filled with content political against opponent Lucius Sergius.",
            'date' : "07 March 2025",
            'views' : "15k Views",
        },
        {
            'id' : 4,
            'img' : '/static/assets/img/blog-4.jpg', 
            'title' : 'Top 10 Free Bootstrap Templates for Your Next Project',
            'desc' : "Think of a news blog that's filled with content political against opponent Lucius Sergius Catilina. Hourly on the day of going live.",
            'date' : '12 Feb 2025',
            'views' : '12k Views',
        },
        {
            'id' : 5,
            'img' : '/static/assets/img/blog-5.jpg', 
            'title' : 'Creating Stunning Landing Pages with Bootstrap: Best Practices',
            'desc' : "Think of a news blog that's filled with content political against opponent Lucius Sergius Catilina. Hourly on the day of going live.",
            'date' : '17 Jan 2025',
            'views' : '33k Views',
        },
        {
            'id' : 6,
            'img' : '/static/assets/img/blog-6.jpg', 
            'title' : 'The Benefits of Using Bootstrap for Your Web Development Projects',
            'desc' : "Think of a news blog that's filled with content political against opponent Lucius Sergius Catilina. Hourly on the day of going live.",
            'date' : '07 March 2025',
            'views' : '15k Views',
        }
    ]
    selected_blog = next((blog for blog in blogs if slugify(blog['title']) == title), None)

    if selected_blog:
        return render_template('pages/blog-detail.html', blog=selected_blog)
    else:
        return "blog not found", 404


@main.route("/contact-us/")
def contact_us():
    return render_template("pages/contact-us.html")


@main.route("/pricing/")
def pricing():
    return render_template("pages/pricing.html")


@main.route("/help-center/")
def help_center():
    return render_template("pages/help-center.html")


@main.route("/comingsoon/")
def comingsoon():
    return render_template("pages/comingsoon.html")


@main.route("/faq/")
def faq():
    return render_template("pages/faq.html")


@main.route("/error/")
def error():
    return render_template("pages/error.html")


@main.route("/elements/")
def elements():
    return render_template("pages/elements.html")


@main.route("/checkout-page/")
def checkout_page():
    return render_template("pages/checkout-page.html")


@main.route("/invoice-page/")
def invoice_page():
    return render_template("pages/invoice-page.html")


@main.route("/privacy-policy/")
def privacy_policy():
    return render_template("pages/privacy-policy.html")


@main.route("/single-helps/")
def single_helps():
    return render_template("pages/single-helps.html")


@main.route("/success-payment/")
def success_payment():
    return render_template("pages/success-payment.html")


@main.route("/viewcart/")
def viewcart():
    return render_template("pages/viewcart.html")
