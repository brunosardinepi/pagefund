$(document).on("click","#form-input",function(event){event.preventDefault();var month=$("#id_birthday_month :selected");var day=$("#id_birthday_day :selected");var year=$("#id_birthday_year :selected");if((month.text()!="---")&&(day.text()!="---")&&(year.text()!="---")){$("#create-form").submit()}else{alert("Please fill in your birthday.")}})