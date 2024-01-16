function ChooseImage(name: string) {
    const theme = document.documentElement.getAttribute("data-theme");
    return `/A.I.D.E/images/${theme}/${name}`
}

export default ChooseImage