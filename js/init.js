(function($){
  $(function(){

    $('.sidenav').sidenav();

  }); // end of document ready

  $(function(enableDark) {
    document.documentElement.setAttribute('theme', enableDark ? 'dark' : 'light');
    localStorage.setItem('theme', enableDark ? 'dark' : 'light');
  });
  
  $(document).ready(function(){
    $('select').formSelect();
    // SWAP ICON ON CLICK
    // Source: https://stackoverflow.com/a/34254979/751570
    $('.dark-toggle').on('click',function(){
      if ($(this).find('i').text() == 'brightness_4'){
          $(this).find('i').text('brightness_high');
      } else {
          $(this).find('i').text('brightness_4');
      }
    });
    
  });
})(jQuery); // end of jQuery name space
