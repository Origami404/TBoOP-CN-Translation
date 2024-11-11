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
	it
) = {
	it
	parbreak()
}
#let p_quote = p_normal
#let p_poetry = p_normal
#let p_img = p_normal
#let p_title(it) = heading(level: 2, it)

#let l_ordered(it) = enum(it)
#let l_ordered_item(it) = enum.item(it)

#let l_unordered(it) = list(it)
#let l_unordered_item(it) = list.item(it)

#let t_footnote(target_label, this_label, it) = super([#link(target_label, it) #label(this_label)])
#let t_footnotecontent = t_footnote

#let t_img = image
