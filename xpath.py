from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from typing import List, Union
import time
import warnings

class EmptyWebElement:
    def __init__(self, Xpath_object, raise_warning:bool = True):
        if raise_warning:
            warnings.warn(f"Warning: Empty web element defined! Xpath: {Xpath_object}")
        self.raise_warning = raise_warning
        self.Xpath_object = Xpath_object
        self.text = None
        self.tag_name = None
        self.get_attribute = lambda attr: None
        self.is_displayed = lambda: None
        self.is_enabled = lambda: None
        self.is_selected = lambda: None
        self.location = None
        self.size = None
        self.rect = None
        self.value_of_css_property = lambda prop: None
        
    def __bool__(self):
        return False

    def find_element(self, *args, **kwargs):
        return EmptyWebElement(self.Xpath_object, raise_warning=self.raise_warning)

    def find_elements(self, *args, **kwargs):
        return []

class Xpath:
    def __init__(
        self,
        driver:webdriver,
        tag:str,
        is_global:bool = False,
        wait:float = 0.0,
        wait_method_single_element = EC.presence_of_element_located,
        wait_method_multiple_elements = EC.presence_of_all_elements_located,
        sleep:float = 0.0,
        raise_warning:bool=False
        ):
        """
        Initialize an XPath builder for constructing complex XPath queries.
        
        Args:
            driver: Selenium WebDriver instance
            tag (str): The HTML tag to target (e.g., 'div', 'a')
            is_global (bool): If True, creates absolute XPath (from root).
                             If False, creates relative XPath (from current node).
            wait: Maximum wait time in seconds (0 for immediate return)
                If > 0, will wait for element to become present
            wait_method: expected_conditions function for wait 
            sleep: time in seconds between element found and return
        """
        # Initialize base XPath (absolute or relative)
        self.xpath = "" if is_global else "."
        self.xpath += f"//{tag}"  # Add target tag

        # define driver
        self.driver = driver
        self.wait = wait
        self.wait_method_single_element = wait_method_single_element
        self.wait_method_multiple_elements = wait_method_multiple_elements
        self.sleep = sleep

        self.raise_warning = raise_warning
        
        # Stores XPath conditions for the main element
        self.arguments = []  

        self.sibling_tag = None
        self.sibling_args = []
        self._sibling_index = None

        # Stores XPath conditions for child elements
        self.children_args = []  

        # Maps condition types to their handler methods
        self.condition_handlers = {
            "contains": self.contains,
            "equals": self.equals,
            "starts_with": self.starts_with,
            "not_equals": self.not_equals,
            "not_in":self.not_in,
            "not":self.not_in,
        }
    
    @property
    def element(self):
        try:
            element = self.get_element()
        except NoSuchElementException:
            element = EmptyWebElement(
                self,
                self.raise_warning # for debugging
            )
        return element
    
    @property
    def elements(self):
        elements = self.get_elements()
        if not elements:
            return []
        return elements

    def _handle_inputs(self, attr):
        """
        Normalizes attribute names to valid XPath format.
        
        Args:
            attr (str): Attribute to normalize (e.g., 'text', 'class', '@href')
            
        Returns:
            str: Proper XPath attribute (e.g., 'text()', '@class')
        """
        if 'text' in attr:
            return 'text()'  # Convert to XPath text function
        elif not attr.startswith("@"):
            return "@" + attr  # Add @ prefix if missing
        return attr
    
    def equals(self, attr, value, _return_arg=False) -> 'Xpath':
        """
        Adds an exact match condition (@attr='value').
        
        Args:
            attr (str): Attribute to match (e.g., 'class', '@href')
            value (str): Exact value to match
            _return_arg (bool): If True, returns the condition instead of storing it
        """
        attr = self._handle_inputs(attr)
        arg = f"{attr}='{value}'"
        
        if _return_arg:
            return arg
        self.arguments.append(arg)
        
        return self

    def not_equals(self, attr, value, _return_arg=False) -> 'Xpath':
        """
        Adds a condition to exclude elements where @attr='value'.

        Args:
            attr (str): Attribute to check (e.g., 'class', '@href')
            value (str): Value to exclude
            _return_arg (bool): If True, returns the condition instead of storing it
        """
        attr = self._handle_inputs(attr)
        arg = f"{attr}!='{value}'" 
        
        if _return_arg:
            return arg
        self.arguments.append(arg)
        
        return self

    def not_in(self, attr, value=None, _return_arg=False) -> 'Xpath':
        """
        Adds a condition to exclude elements without a specific attribute 
        or elements where @attr does not have a specific value.

        Args:
            attr (str): Attribute to check (e.g., 'class', '@href')
            value (str, optional): Value to exclude (default is None)
            _return_arg (bool): If True, returns the condition instead of storing it
        """
        attr = self._handle_inputs(attr)
        arg = f"not({attr})" if value is None else f"not({attr}='{value}')"
        
        if _return_arg:
            return arg
        self.arguments.append(arg)
        
        return self

    def contains(self, attr, value, _return_arg=False) -> 'Xpath':
        """
        Adds a partial match condition (contains(@attr, 'value')).
        
        Args:
            attr (str): Attribute to check
            value (str): Substring to find
            _return_arg (bool): If True, returns the condition instead of storing it
        """
        attr = self._handle_inputs(attr)
        arg = f"contains({attr}, '{value}')"
        
        if _return_arg:
            return arg
        self.arguments.append(arg)
        
        return self

    def starts_with(self, attr, value, _return_arg=False) -> 'Xpath':
        """
        Adds a prefix match condition (starts-with(@attr, 'value')).
        
        Args:
            attr (str): Attribute to check
            value (str): Prefix to match
            _return_arg (bool): If True, returns the condition instead of storing it
        """
        attr = self._handle_inputs(attr)
        arg = f"starts-with({attr}, '{value}')"
        
        if _return_arg:
            return arg
        self.arguments.append(arg)
        
        return self

    def add_condition(self, condition, attr, value, _return_arg=False) -> 'Xpath':
        """
        Adds a condition to the main element.
        
        Args:
            condition (str): Type of condition ('contains', 'equals', 'starts_with', 'not_equals')
            attr (str): Attribute to check
            value (str): Value to match
        """
        attr = self._handle_inputs(attr)
        func = self.condition_handlers[condition]
        arg = func(attr, value, _return_arg=True)
        if _return_arg:
            return arg
        self.arguments.append(arg)
        
        return self

    def child_condition(self, condition, attr, value) -> 'Xpath':
        """
        Adds a condition for any descendant child element.
        
        Args:
            condition (str): Type of condition ('contains', 'equals', 'starts_with', 'not_equals')
            attr (str): Attribute to check
            value (str): Value to match
        """
        attr = self._handle_inputs(attr)
        func = self.condition_handlers[condition]
        arg = func(attr, value, _return_arg=True)
        self.children_args.append(arg)
        
        return self

    def not_condition(self, condition, attr, value) -> 'Xpath':
        """"""
        attr = self._handle_inputs(attr)
        func = self.condition_handlers[condition]
        arg = func(attr, value, _return_arg=True)
        self.arguments.append(f"not({arg})")

    def following_sibling(self, sibling_tag:str = None, *args, **kwargs) -> 'Xpath':
        """
        Define tag and condition for a following sibling.
        If not defined, std tag is defined as '*'.
        
        Args:
            tag (str): tag for following sibling
            condition (str): Type of condition ('contains', 'equals', 'starts_with', 'not_equals')
            attr (str): Attribute to check
            value (str): Value to match
        """
        if sibling_tag is None:
            sibling_tag = "*"
        self.sibling_tag = sibling_tag
        if args or kwargs:
            arg = self.add_condition(*args, **kwargs, _return_arg=True)
            self.sibling_args.append(arg)
            
        return self
    
    def sibling_condition(self, condition, attr, value) -> 'Xpath':
        """
        Adds a condition for the wanted sibling element.
        Is it not obligary to define 'following_sibling' before calling
        this method

        Args:
            condition (str): Type of condition ('contains', 'equals', 'starts_with', 'not_equals')
            attr (str): Attribute to check
            value (str): Value to match
        """
        attr = self._handle_inputs(attr)
        func = self.condition_handlers[condition]
        arg = func(attr, value, _return_arg=True)
        self.sibling_args.append(arg)
        
        return self

    def sibling_index(self, index:int) -> 'Xpath':

        self._sibling_index = index
        
        return self

    def get_element(
        self,
        wait: float = None,
        wait_method = None,
        sleep: float = None
    ) -> WebElement:
        """
        Find and return a single web element using the stored XPath.
        
        Args:
            
            wait: Maximum wait time in seconds (0 for immediate return)
                If > 0, will wait for element to become present
            wait_method: expected_conditions function for wait 
            sleep: time in seconds between element found and return
        
        Returns:
            WebElement: The first matching element found
            
        Raises:
            TimeoutException: If wait > 0 and element not found within timeout
            NoSuchElementException: If wait = 0 and element not found immediately
            
        Example:
            xpath = Xpath("button", contains=[{"attr": "text", "value": "Submit"}])
            try:
                submit_btn = xpath.get_element(driver, wait=5.0)
                submit_btn.click()
            except (TimeoutException, NoSuchElementException):
                print("Submit button not found")
        """
        xpath = self.get
        driver = self.driver
        wait = self.wait if wait is None else wait
        wait_method = self.wait_method_single_element if wait_method is None else wait_method
        sleep = self.wait if sleep is None else sleep
        if wait > 0:
            element = WebDriverWait(driver, wait).until(
                        wait_method((By.XPATH, xpath))
            )
            time.sleep(sleep)
            return element
        
        element = driver.find_element(By.XPATH, xpath)
        time.sleep(sleep)
        return element

    def get_elements(
        self,
        wait: float = None,
        wait_method = None,
        sleep: float = None
        ) -> List[WebElement]:
        """
        Find and return all matching web elements using the stored XPath.
        
        Args:
            
            wait: Maximum wait time in seconds (0 for immediate return)
                If > 0, will wait for at least one element to become present
            wait_method: expected_conditions function for wait 
            sleep: time in seconds between element found and return

        Returns:
            List[WebElement]: All matching elements (empty list if none found)
            
        Raises:
            TimeoutException: If wait > 0 and no elements found within timeout
            
        Example:
            xpath = Xpath("li", contains=[{"attr": "class", "value": "item"}])
            try:
                items = xpath.get_elements(driver, wait=3.0)
                print(f"Found {len(items)} items")
            except TimeoutException:
                print("No items found within timeout period")
        """
        xpath = self.get
        driver = self.driver
        wait = self.wait if wait is None else wait
        wait_method = self.wait_method_multiple_elements if wait_method is None else wait_method
        sleep = self.wait if sleep is None else sleep
        if wait > 0:
            # Wait for at least one element to be present
            elements = WebDriverWait(driver, wait).until(
                wait_method((By.XPATH, xpath))
            )
            time.sleep(sleep)
            return elements
        elements = driver.find_elements(By.XPATH, xpath)
        time.sleep(sleep)
        return elements

    def element_exists(self, wait:float=None) -> bool:
        """
        Check if element exists, with optional waiting.
        
        Args:
            
            wait: Maximum wait time in seconds (0 for no wait)
            
        Returns:
            bool: True if element exists, False otherwise
            
        Example:
            xpath = Xpath("div")
            exists = xpath.element_exists(driver, wait=5.0)  # Wait up to 5 seconds
        """
        xpath = self.get
        driver = self.driver
        wait = self.wait if wait is None else wait
        if wait > 0:
            try:
                WebDriverWait(driver, wait).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                    )
                return True
            except TimeoutException:
                return False
        try:
            driver.find_element(By.XPATH, xpath)
            return True
        except NoSuchElementException:
            return False

    def click_element(
        self,
        wait :float = None,
        wait_method = None,
        sleep:float = None,
        return_element:bool = False
        ):
        """
        Clicks element based on 'get_element' method.

        if return_element (default False) is True, returns the element.
        """
        driver = self.driver
        wait = self.wait if wait is None else wait
        wait_method = self.wait_method_single_element if wait_method is None else wait_method
        sleep = self.wait if sleep is None else sleep
        element = self.get_element(
            wait=wait,
            wait_method=wait_method,
            sleep=sleep
        )

        element.click()

        if return_element:
            return element

    def force_click(self, wait:float=None, _counter=0, _error=None) -> None:
        driver = self.driver
        wait = self.wait if wait is None else wait
        if _counter > 10:
            raise StopIteration(f"Force click has not succeeded. Exception {_error}")
        element = self.get_element(wait=wait)
        try:
            element.click()
        except Exception as e:
            time.sleep(1)
            self.force_click(driver, wait, _counter+1, _error=e)

    def __str__(self):
        return self.get

    @property
    def get(self):
        """
        Constructs the final XPath by combining all conditions.
        
        Returns:
            str: Complete XPath query with all conditions
        """
        # Combine conditions for the main element
        arg_str = " and ".join(self.arguments)  
        r_xpath = self.xpath

        if arg_str:
            r_xpath += f"[{arg_str}]"

        # Combine conditions for child elements 
        if self.children_args:
            children_arg_str = " and ".join(self.children_args)
            r_xpath += f"[.//*[{children_arg_str}]]"
        
        if self.sibling_tag:
            r_xpath += f"/following-sibling::{self.sibling_tag}"
        
            # if self.children_args:
            #     children_arg_str = " and ".join(self.children_args)
            #     r_xpath += f"[.//*[{children_arg_str}]]"
            
            if self._sibling_index:
                r_xpath += f"[{self._sibling_index}]"


        return r_xpath


# Example usage
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
