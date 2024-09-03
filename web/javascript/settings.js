document.getElementById("ram-range").addEventListener("input", function() {
    document.getElementById("ram-input").value = this.value;
});

document.getElementById("ram-input").addEventListener("blur", function() {
    const min = parseInt(this.min);
    const max = parseInt(this.max);
    let value = parseInt(this.value);

    if (value < min) {
        value = min;
    } else if (value > max) {
        value = max;
    }

    this.value = value;
    document.getElementById("ram-range").value = value;
});

document.getElementById("type-change-skin").addEventListener("input", function() {
    if (this.value == 1) {
        document.getElementById("input-id-document-plastic-surgery").style.display = "block";
    } else {
        document.getElementById("input-id-document-plastic-surgery").style.display = "none";
    }
});