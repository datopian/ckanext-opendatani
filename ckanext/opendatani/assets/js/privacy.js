function privacyFunction(){
    var privacy = document.getElementById("field-privacy").checked;
    if (privacy === true) {
      return true
    }
    else {
      alert('Consent to process has not been provided, user account cannot be created');
      return false
    }
}