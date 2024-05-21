<script>
var visible = 1;
function nextpage() {
    document.getElementById("uudis" + visible).style["display"] = "none";
    visible += 1;
    if (visible > 5) { visible = 1; }
    document.getElementById("uudis" + visible).style["display"] = "block";
}

function prevpage() {
    document.getElementById("uudis" + visible).style["display"] = "none";
    visible -= 1;
    if (visible < 1) { visible = 5; }
    document.getElementById("uudis" + visible).style["display"] = "block";
}
document.getElementById("uudis" + visible).style["display"] = "block";</script>