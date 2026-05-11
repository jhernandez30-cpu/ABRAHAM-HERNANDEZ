/*!
 * Generated using the Bootstrap Customizer (<none>)
 * Config saved to config.json and <none>
 */

 (function($) {

  "use strict";

  // ------------------------------------------------------------------------------ //
  // get path relative to javascript
  // ------------------------------------------------------------------------------ //
 
 $(document).ready(function(){

  if ($.fn.slick && $('.service-slider').length) {
    $('.service-slider').each(function() {
      var $slider = $(this);
      var $shell = $slider.closest('.service-carousel-shell');

      $slider.slick({
        slidesToShow: 3,
        slidesToScroll: 1,
        autoplaySpeed: 2000,
        dots: true,
        prevArrow: $shell.find('.service-carousel-prev'),
        nextArrow: $shell.find('.service-carousel-next'),
        responsive: [
          {
            breakpoint: 1500,
            settings: {
              slidesToShow: 2,
              slidesToScroll: 2,
            }
          },
          {
            breakpoint: 800,
            settings: {
              slidesToShow: 1,
              slidesToScroll: 1,
              arrows: false,
            }
          }
        ]
      });

      $shell.addClass('is-carousel-ready');
    });
  }

  if ($.fn.slick && $('.experience-slider').length) {
	  $('.experience-slider').slick({
          autoplay: false,
          autoplaySpeed: 4000,
          fade: true,
          prevArrow: $('.prev'),
          nextArrow: $('.next'),
	});
  }

  $('.menu-toggle').on('click', function(event) {
    event.preventDefault();
    event.stopPropagation();
    $('#navigation').toggleClass('menu-bar');
    $(this).attr('aria-expanded', $('#navigation').hasClass('menu-bar'));
  });

  $('#navigation .menu-list a').on('click', function() {
    if (window.innerWidth <= 1080) {
      $('#navigation').removeClass('menu-bar');
      $('.menu-toggle').attr('aria-expanded', 'false');
    }
  });

});

const tabs = document.querySelectorAll('[data-tab-target]')
const tabContents = document.querySelectorAll('[data-tab-content]')

tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    const target = document.querySelector(tab.dataset.tabTarget)
    if (!target) return
    tabContents.forEach(tabContent => {
      tabContent.classList.remove('active')
    })
    tabs.forEach(tab => {
      tab.classList.remove('active')
    })
    tab.classList.add('active')
    target.classList.add('active')
  })
});



})(jQuery);
