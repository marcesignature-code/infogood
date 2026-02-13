// For Date

$(function() {
    const input = document.getElementById("input");
    if (input) {
        rome(input, { time: false });
    }
});


// Check In & Check Out Daterange Script
$(function() {
$('input[name="checkout"]').daterangepicker({
    singleDatePicker: true,
});
    $('input[name="checkout"]').val('');
    $('input[name="checkout"]').attr("placeholder","Check Out");
});
$(function() {
$('input[name="checkin"]').daterangepicker({
    singleDatePicker: true,
    
});
    $('input[name="checkin"]').val('');
    $('input[name="checkin"]').attr("placeholder","Check In");
});


// For counter

try {
const counters = document.querySelectorAll('.counter-value');
const speed = 2500; // The lower the slower

counters.forEach(counter => {
    const updateCount = () => {
    const target = +counter.getAttribute('data-target');
    const count = +counter.innerText;
    
    // Calculate increment to reach target in the given speed
    let inc = target / speed;
    
    // Make sure increment is at least 1
    if (inc < 1) inc = 1;

    // If the counter hasn't reached the target, update it
    if (count < target) {
        counter.innerText = Math.min(count + inc, target).toFixed(0); // Ensure not exceeding target
        // Use requestAnimationFrame for smoother and better performance
        requestAnimationFrame(updateCount);
    } else {
        counter.innerText = target; // Set to target when done
    }
    };

    updateCount();
});
} catch (err) {
console.error("Error in counter script:", err); // Log any errors for debugging
}


// Filter Search

function openFilterSearch() {
    document.getElementById("filter_search").style.display = "block";
}
function closeFilterSearch() {
    document.getElementById("filter_search").style.display = "none";
}


// showbutton

$(document).ready(function(){
    $("#showbutton").click(function(){
    $("#showing").slideToggle("slow");
});
});


// back-to-top

window.onscroll = function () {
    scrollFunction();
};

function scrollFunction() {
    const mybutton = document.getElementById("back-to-top");
    if (mybutton !== null) {
        if (document.body.scrollTop > 500 || document.documentElement.scrollTop > 500) {
            mybutton.classList.add("block");
            mybutton.classList.remove("hidden");
        } else {
            mybutton.classList.add("hidden");
            mybutton.classList.remove("block");
        }
    }
}

function topFunction() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
}


//  Choices Js

document.addEventListener('DOMContentLoaded', function () {
    const selectIds = ['my-select', 'my-select2', 'my-select3', 'my-select4', 'my-select5', 'my-select6', 'my-select7', 'my-select8', 'my-select9', 'my-select10', 'my-select11', 'my-select12', 'my-select13', 'my-select14', 'my-select15', 'my-select16', 'my-select17', 'my-select18'];

    selectIds.forEach(id => {
        const el = document.getElementById(id);
        if (el && (el.tagName === 'SELECT' || 
                   (el.tagName === 'INPUT' && (el.type === 'text' || el.type === 'search')))) {

            // Custom config only for my-select3
            const config = (id === 'my-select3') ? {
                placeholder: true,
                placeholderValue: 'Advanced features',
                removeItemButton: true,
                renderSelectedChoices: 'always'
            } : {};

            new Choices(el, config);
        }
    });
});