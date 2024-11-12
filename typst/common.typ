#let indent-width = 2em
#let lang-variant = "zh" 

#let select-lang-variant(..it) = {
  let it = it.pos()
  if it.len() == 1 {
    it.at(0)
  } else {
    let english-it = it.at(0)
    let chinese-it = it.at(1)

    if lang-variant == "zh" {
      chinese-it
    } else if lang-variant == "en" {
      english-it
    } else if lang-variant == "zh-en" {
      [#par(english-it) #par(chinese-it)]
    }
  }
}

#let character(it) = {
  it
  pagebreak()
}
#let l_section(it) = it
#let p_normal(
  word_indent: "first-line",
  para_indent: 0,
  center: false,
  italic: false,
  bold: false,
  right: false,
  spacing: 1em,
  ..it
) = {

  let it = select-lang-variant(..it)

  let it = if center and right {
    align(center + right, it)
  } else if center {
    align(alignment.center, it)
  } else if right {
    align(alignment.right, it)
  } else {
    it
  }

  let it = if italic and bold {
    text(style: "italic", weight: "bold", it)
  } else if italic {
    text(style: "italic", it)
  } else if bold {
    text(weight: "bold", it)
  } else {
    it
  }

  let first-line-indent-by-word = if word_indent == "first-line" {
    indent-width
  } else {
    0pt
  }
  let hanging-indent-by-word = if word_indent == "non-first-line" {
    indent-width
  } else {
    0pt
  }

  let first-line-indent = first-line-indent-by-word + para_indent * indent-width
  let hanging-indent = hanging-indent-by-word + para_indent * indent-width

  par(
    first-line-indent: first-line-indent, 
    hanging-indent: hanging-indent, 
    spacing: spacing,
    it
  )
}
#let p_poetry(..it) = p_normal(word_indent: "none", para_indent: 1, italic: true, ..it)
#let p_quote(..it) = p_normal(word_indent: "none", para_indent: 1, italic: true, spacing: 2.5em, ..it)
#let p_img(..it) = p_normal(center: true, italic: true, ..it)
#let p_title(..it) = heading(level: 2, select-lang-variant(..it))

#let l_ordered(..it) = enum(indent: indent-width, ..it)
#let l_ordered_item(it) = enum.item(it)

#let l_unordered(..it) = list(indent: indent-width, ..it)
#let l_unordered_item(it) = list.item(it)

#let t_footnote(id, it) = {
  let target_label = label("nr" + str(id))
  let this_label = label("nt" + str(id))

  super[#link(target_label, it) #this_label]
}
#let t_footnotecontent(id, it) = {
  let target_label = label("nt" + str(id))
  let this_label = label("nr" + str(id))

  super[#link(target_label, it) #this_label]
}

#let t_img = image
