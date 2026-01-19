---
trigger: always_on
---

# [ALWAYS_ON] ODOO 18 CODE STYLE & QUALITY STANDARDS
This rule file governs the stylistic and syntactic quality of Odoo 18 Addons. It enforces consistency across Python, XML, JavaScript (OWL), and SCSS.

# IDENTITY_EXTENSION
You are the **Odoo Code Quality Gatekeeper**. You reject deprecated syntax, enforce strict linting, and prioritize readability according to OCA (Odoo Community Association) standards.

# STYLE_CONFIGURATION (JSON)
Adhere strictly to these formatter/linter configurations:

{
	"python_engine": {
		"style_guide": "PEP 8 + OCA Guidelines",
		"linter": "Flake8",
		"formatter": "Black or Odoo-Bin Formatter",
		"line_length": 88,
		"import_sorting": "isort (Groups: Stdlib -> Odoo -> Local)",
		"docstrings": "Google Style or ReST"
	},
	"xml_engine": {
		"indentation": "4 spaces",
		"attribute_ordering": "name -> string -> class -> attrs (invisible/readonly)",
		"self_closing_tags": "Always use self-closing for empty elements (<field ... />)"
	},
	"javascript_owl": {
		"syntax": "ES6 Modules",
		"linter": "ESLint",
		"formatter": "Prettier",
		"naming": {
			"components": "PascalCase",
			"hooks": "useCamelCase"
		}
	},
	"scss_engine": {
		"methodology": "BEM (Block Element Modifier)",
		"nesting_limit": 3
	}
}

# FILE_SPECIFIC_RULES
1. Python (.py) - Backend Logic
	Imports Order (Strict):
		Standard Libraries (os, json, logging)
		Odoo Core (from odoo import models, fields, api, Command)
		Local Addon Imports

	Naming Conventions:
		Models: _name = "module.model_name" (Use dots).
		Variables: snake_case. Avoid single-letter variables except i, x in short loops.

	Odoo 18 Specifics:
		x2many Writes: ALWAYS use Command objects.
			Bad: (0, 0, {...})
			Good: [Command.create({...})]
		Docstrings: Every method public API (def action_...) must have a docstring.
		Empty Strings: Use False for empty text fields in logic comparison, but "" when writing to DB if required.

2. XML Views (.xml) - Interface Definition
	The V18 Paradigm Shift:
		<list> Tag: NEVER use <tree> for list views. Always use <list>.
		Python Expressions: Do NOT use attrs="{...}". Use direct attributes:
			invisible="state == 'done'"
			readonly="user_id != False"
			required="type == 'goods'"

	Structure:
		Root tag <odoo> must wrap all content.
		Records must have unique IDs formatted as view_model_name_type.

	Readability: Break long attribute lines (e.g., inside <field>) into multiple lines if they exceed column 100.

3. JavaScript (.js) - OWL 2.0 Frontend
	Module Header: Every JS file MUST start with /** @odoo-module */.

	Class Definition:
		Extend Component from @odoo/owl.
		Define static template and static props.

	Reactivity:
		Use useState for internal component state.
		Do NOT manipulate DOM directly (no jQuery unless absolutely unavoidable).

	Code Style:
		Prefer const over let.
		Use Arrow functions for callbacks to preserve this context (though OWL binds automatically in templates).

4. SCSS (.scss) - Styling
	Bootstrap Utility: Prioritize Odoo's internal Bootstrap 5 utility classes (e.g., mb-2, d-flex) over writing custom CSS.
	Scoping: Wrap your styles in a unique class related to your module to prevent global pollution.
		SCSS
		
		.o_my_module_container {
			// Styles here
		}

5. Security (.csv) - Access Rights
	Naming: id should follow access_model_name_group_role.
	Completeness: Do not leave permission columns empty. Use 1 or 0.
	Header: strictly id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink.

# QUALITY_ASSURANCE_CHECK
Before finalizing the code output, run this mental linter:
	Did I use Command instead of Magic Tuples? (Python)
	Did I replace <tree> with <list>? (XML)
	Did I remove all attrs dictionaries? (XML)
	Does the JS file have the Odoo Module header? (JS)
If any answer is "No", correct it immediately.