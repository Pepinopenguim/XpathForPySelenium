# XpathForPySelenium
Python helper class designed to simpify the creation of complex XPath queries and management of Selenium WebElements. Uses Builder Pattern to quickly create complex but easily readable xpath patterns dynamically. Also compatible with explicit waits, and handling of missing elements

## Features

* **Fluent API:** Chain methods to build complex XPaths (e.g., `.contains()`, `.following_sibling()`) without writing raw string queries.
* **Automatic Attribute Handling:** Automatically handles `@` prefixes for attributes and normalizes `text` inputs.
* **Integrated Waits:** Built-in support for `WebDriverWait` and `expected_conditions` to reduce boilerplate code.
* **Null Object Pattern:** Returns an `EmptyWebElement` instead of raising exceptions immediately when elements are missing, allowing for safer logic flow.
* **Sibling & Child Targeting:** Easily target elements based on their relationship to other nodes (children, following siblings).

## Dependencies

* Python 3.x
* Selenium

```bash
pip install selenium

```

## Installation

Simply copy the `xpath.py` file into your project directory and import the `Xpath` class.

```python
from xpath import Xpath

```

## Usage

### 1. Initialization

Initialize the `Xpath` object with your WebDriver instance and the target HTML tag.
Use`*` for a generic tag if you so please 

```python
from selenium import webdriver
from xpath import Xpath

driver = webdriver.Chrome()

# Target all <div> elements
my_xpath = Xpath(driver, "div") 

```

### 2. Building Queries

You can chain methods to refine your selection. The class supports `contains`, `equals`, `starts_with`, `not_equals`, and `not_in`.

**Example: Find a button with specific text and class**

```python
# Generates: //button[contains(text(), 'Submit') and @class='btn-primary']
submit_btn = Xpath(driver, "button")\
    .contains("text", "Submit")\
    .equals("class", "btn-primary")

```

**Example: Find a div that does NOT contain a specific ID**

```python
# Generates: //div[not(@id='exclude-me')]
content = Xpath(driver, "div").not_in("id", "exclude-me")

```

### 3. Parent/Child & Sibling Relationships

You can filter elements based on their children or navigate to siblings.

**Example: Find a div that contains a specific span child**

Note that this selects a parent given the characteristcs of a child, not vice-versa

```python
# Generates: //div[.//*[contains(@class, 'highlight')]]
container = Xpath(driver, "div").child_condition("contains", "class", "highlight")

```

**Example: Find an input field following a specific label**

```python
# Generates: //label[text()='Username']/following-sibling::input
username_input = Xpath(driver, "label")\
    .equals("text", "Username")\
    .following_sibling("input")

```

**Example: Find a specific div element with specific `span` child, then find that specific child**
(assume just the span declaration would find other unwanted spans)

```python
# We find a div that has the class 'container' AND contains the specific child we want
container_xpath = Xpath(driver, "div")\
    .equals("class", "container")\
    .child_condition("contains", "text", "Resources")

# Get the WebElement for the container
container_element = container_xpath.element 

# 2. Find the CHILD element (The Target)
# We pass 'container_element' instead of 'driver' to restrict the search to just this box
wanted_span = Xpath(container_element, "span")\
    .contains("text", "Resources")

# This will return the actual span
final_element = wanted_span.element

# this is more powerfull than writing an extremely long xpath
```

### 4. Retrieving Elements & Actions

Once the path is built, you can retrieve the standard Selenium `WebElement` or perform actions directly.

```python
# Get a single element (returns WebElement)
element = my_xpath.get_element()

# Get all matching elements (returns List[WebElement])
elements = my_xpath.get_elements()

# Click with automatic wait
my_xpath.click_element(wait=5.0)

# Check existence (returns bool)
if my_xpath.element_exists(wait=2.0):
    print("Element found!")

```

### 5. Using Waits

You can define wait times during initialization or when calling action methods.

```python
# Set default wait of 10 seconds for this locator
loader = Xpath(driver, "div", wait=10.0).equals("class", "loader")

# Override wait for a specific action
loader.get_element(wait=5.0) 

```

### 6. Quick prints for debugging

You can test all xpaths before adding to code, using the print command on the class itself, so you can copy and test directly on browser.
For this, I recommend using the xpath.py file itself, under ´__name__ == "__main__"´, setting driver as `None`

```python
if __name__ == "__main__":
    some_xpath = Xpath(None, "div")\
        .contains("class", "example")\
        .child_condition("equals", "data-id", "123")\
        .following_sibling("span")\
        .sibling_condition("starts_with", "class", "label")
    
    print(some_xpath)
    # should return:
    # ".//div[contains(@class, 'example')][.//*[@data-id='123']]/following-sibling::span"
    # I have no idea if this is valid xpath, but it looks complex enough
```

## EmptyWebElement Handling

To prevent your script from crashing when an element is not found, the `element` property returns an `EmptyWebElement` if the search fails. This object evaluates to `False` in boolean checks and safely absorbs method calls. Raises warnings when created.

```python
# looks for a club with name Palmeiras that has at 'least one mundial'
club = Xpath(driver, "FootballClub")\
    .equals("name", "Palmeiras")
    .contains("mundial", "at least one")\
    .element
# of course, this will result in no matches
if club:
    club.click() # Will not execute
else:
    print("Element not found, but script continues safely.")

```

## API Reference

### `Xpath` Class

* **`__init__(driver, tag, is_global=False, wait=0.0, ...)`**: Constructor.
* **`equals(attr, value)`**: Adds `[@attr='value']`.
* **`contains(attr, value)`**: Adds `[contains(@attr, 'value')]`.
* **`starts_with(attr, value)`**: Adds `[starts-with(@attr, 'value')]`.
* **`child_condition(condition, attr, value)`**: filters parent based on child attributes.
* **`following_sibling(sibling_tag)`**: Navigate to the following sibling.
* **`get_element(wait=None)`**: Returns the found WebElement.
* **`click_element(wait=None)`**: Clicks the element.

### `EmptyWebElement` Class

A dummy class that mimics `WebElement` behavior but does nothing. Used to avoid `AttributeError: 'NoneType' object has no attribute...`.
