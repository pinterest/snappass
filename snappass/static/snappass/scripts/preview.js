(function () {

  $('#openSecret').click(function () {
    var form = $('<form/>')
      .attr('id', 'openSecretForm')
      .attr('method', 'post');
    form.appendTo($('body'));
    form.submit();
  });
})();