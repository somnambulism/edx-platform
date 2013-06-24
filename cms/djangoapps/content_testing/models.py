"""
Django models used to store and manipulate content tests
"""

from django.db import models
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from contentstore.views.preview import get_preview_module
from mitxmako.shortcuts import render_to_string  # pylint: disable=F0401
from lxml import etree
from copy import deepcopy
import pickle


def hash_xml(tree):
    """
    create a has of the etree xml element solely based on the text
    of the xml.
    """
    tree = deepcopy(tree)
    remove_xml_ids(tree)
    return etree.tostring(tree).__hash__()


def remove_xml_ids(tree):
    """
    recursivly remove all attribsthat end in `id`
    """
    remove_ids(tree.attrib)
    for child in tree:
        remove_xml_ids(child)


def remove_ids(attribs):
    """
    remove all keys that end in `id` or are `size`
    """
    for k in attribs:
        if k[-2:] == 'id' or k == 'size':
            attribs.pop(k)


CACHE_MODULESTORE = {}
CACHE_ON = False


class ContentTest(models.Model):
    """
    Model for a user-created test for a capa-problem
    """

    # the problem to test (location)
    # future-proof against long locations?
    problem_location = models.CharField(max_length=100)

    # what the problem should evaluate as (correct or incorrect)
    # TODO: make this a dict of correctness for each response
    should_be = models.CharField(max_length=20)

    # the current state of the test
    verdict = models.TextField()

    # pickle of dictionary that is the stored input
    response_dict = models.TextField()

    # messeges for verdict
    ERROR = "ERROR"
    PASS = "Pass"
    FAIL = "Fail"
    NONE = "Not Run"

    def __init__(self, *arg, **kwargs):
        """
        Overwrite default __init__ behavior to pickle the dictionary and
            save in a new field so we know if the response_dict gets overwritten
        """

        if 'response_dict' not in kwargs:
            kwargs['response_dict'] = {}

        kwargs['response_dict'] = pickle.dumps(kwargs['response_dict'])
        super(ContentTest, self).__init__(*arg, **kwargs)

        # store the old dict for later comparison (only update if it is changed)
        self._old_response_dict = self.response_dict

    @property
    def capa_problem(self):
        """
        create the capa_problem.  In teh process override the render_html methods of the
        response objects for the purpose of inserting html into the problem.  This is for
        the possible future feature of specifying verdict-per-response.
        """

        # create a preview capa problem
        lcp = self.capa_module().lcp

        # override html methods
        # for key in lcp.responders:

            # define wrapper
            # def wrapper(func):
            #     def html_wrapper(*args, **kwargs):

            #         # make surrounding div for each response
            #         div = etree.Element('div')
            #         div.set('class', "verdict-response-wrapper")

            #         # should_be choice for this response
            #         buttons = etree.fromstring(self._should_be_buttons(self.should_be))

            #         div.append(func(*args, **kwargs))
            #         div.append(buttons)
            #         return div

            #     return html_wrapper

            # execute the override
            # lcp.responders[key].render_html = wrapper(lcp.responders[key].render_html)
        return lcp

    def capa_module(self):
        """
        resturns a preview instance of the capa module pointed to by
        self.problem_location
        """
        # if caching is on, try to get from chach
        if CACHE_ON:
            try:
                preview_module = CACHE_MODULESTORE[self.pk]

            except KeyError:
                # create a preview of the capa_module
                preview_module = self.construct_preview_module()

                # add it to the cache
                CACHE_MODULESTORE[self.pk] = preview_module

        else:
            # create a preview of the capa_module
            preview_module = self.construct_preview_module()

        return preview_module

    def construct_preview_module(self):
        """
        construct a new preview capa module
        """
        # create a preview of the capa_module
        problem_descriptor = modulestore().get_item(Location(self.problem_location))
        preview_module = get_preview_module(0, problem_descriptor)

        # edit the module to have the correct test-student-responses
        # and (in the future support randomization)
        new_lcp_state = preview_module.get_state_for_lcp()  # pylint: disable=E1103
        new_lcp_state['student_answers'] = self._get_response_dictionary()
        preview_module.lcp = preview_module.new_lcp(new_lcp_state)  # pylint: disable=E1103

        return preview_module

    def save(self, *arg, **kwargs):
        """
        Overwrite default save behavior with the following features:
            > If the children haven't been created, create them
            > If the response dictionary is being changed, update the children
        """

        # if we are changing something, reset verdict by default
        if not('dont_reset' in kwargs):
            self.verdict = self.NONE
        else:
            kwargs.pop('dont_reset')

        # if we have a dictionary
        # import nose; nose.tools.set_trace()
        if hasattr(self, 'response_dict'):
            #if it isn't pickled, pickle it.
            if not(isinstance(self.response_dict, basestring)):
                self.response_dict = pickle.dumps(self.response_dict)

                # if it is new, update children
                if self.response_dict != self._old_response_dict:
                    self._update_dictionary(pickle.loads(self.response_dict))

        # save it as normal
        super(ContentTest, self).save(*arg, **kwargs)

        # look for children
        children = Response.objects.filter(content_test=self.pk)

        # if there are none, try to create them
        if children.count() == 0:
            self._create_children()

    def run(self):
        """
        run the test, and see if it passes
        """

        # process dictionary that is the response from grading
        grade_dict = self._evaluate(self._get_response_dictionary())

        # compare the result with what is should be
        self.verdict = self._make_verdict(grade_dict)

        # write the change to the database and return the result
        self.save(dont_reset=True)
        return self.verdict

    def get_html_summary(self):
        """
        return an html summary of this test
        """
        # check for changes to the capa_problem
        self.rematch_if_necessary()

        # retrieve all inputs sorted first by response, and then by order in that response
        sorted_inputs = self.input_set.order_by('response_index', 'input_index').values('answer')  # pylint: disable=E1101
        answers = [input_model['answer'] or '-- Not Set --' for input_model in sorted_inputs]

        # construct a context for rendering this
        context = {'answers': answers, 'verdict': self.verdict, 'should_be': self.should_be}
        return render_to_string('content_testing/unit_summary.html', context)

    def get_html_form(self):
        """
        return html to put into form for editing and creating
        """
        # check for changes to the capa_problem
        self.rematch_if_necessary()

        # html with the inputs blank
        html_form = self.capa_problem.get_html()

        # remove any forms that the html has
        # as far as I can tell these are only used for
        # multiple choice and dropdowns (although these are not
        # the ones people will really be testing)
        # THIS STEP IS BASICALLY A COMPLETE HACK
        import re
        remove_form_open = r"(<form)[^>]*>"
        remove_form_close = r"(/form)"
        html_form = re.sub(remove_form_open, '', html_form)
        html_form = re.sub(remove_form_close, '', html_form)

        # add the radio buttons
        html_form = html_form + self._should_be_buttons(self.should_be)
        return html_form

    def rematch_if_necessary(self):
        """
        Rematches itself to its problem if it no longer matches.
        Reassigns hashes to response models if they no longer
        match but the structure still does.
        """

        # if this contentTest has not been saved, no need to check
        if self.pk is None:
            return

        # clear cache and turn caching on

        global CACHE_ON  # pylint: disable=W0603
        CACHE_ON = True
        CACHE_MODULESTORE.clear()

        try:
            if not self._still_matches():
                self._rematch()

            elif not self._still_hashes_match():
                self._reassign_hashes()
        except:
            raise

        finally:
            # clear cache and turn caching off
            CACHE_ON = False
            CACHE_MODULESTORE.clear()

#======= Private Methods =======#

    def _still_matches(self):
        """
        Returns true if the test still corresponds to the structure of the
        problem
        """

        # if there are no longer the same number, not a match.
        if not(self.response_set.count() == len(self.capa_problem.responders)):  # pylint: disable=E1101
            return False

        # loop through response models, and check that they match
        all_match = True
        for resp_model in self.response_set.all():  # pylint: disable=E1101
            if not resp_model.still_matches():
                all_match = False
                break

        return all_match

    def _still_hashes_match(self):
        """
        Returns true if all the hashes still match, and false if they dont
        (this indicates the problem has been edited)
        """

        all_hashes_match = True
        for resp_model in self.response_set.all():  # pylint: disable=E1101
            if not resp_model.still_hashes_match():  # pylint: disable=E1101
                all_hashes_match = False
                break

        return all_hashes_match

    def _rematch(self):
        """
        corrects structure to reflect the state of the capa problem
        """

        # create dictionary of response models based on their hashes
        # NOTE: duplicates will be discarded (essentially made blank)
        resp_models = self.response_set.all()  # pylint: disable=E1101
        model_dict = {}
        for model in resp_models:
            model_dict[model.xml_hash] = model

        # reassign models to responders based on hashes
        used_models = []
        for responder in self.capa_problem.responders.values():
            responder_hash = hash_xml(responder.xml)

            # try to get the already existant model
            try:
                resp_model = model_dict.pop(responder_hash)

                # re-sync ids and count this model as used
                resp_model.rematch(responder)
                used_models.append(resp_model)

            # make a new one if necessary
            except KeyError:
                self._create_child(responder)

        # delete unnused models
        for model in resp_models:
            if model not in used_models:
                model.delete()

        # remake the dictionary
        self._remake_dict_from_children()

    def _reassign_hashes(self):
        """
        tell all children to reassign their hashes
        """

        for resp_model in self.response_set.all():  # pylint: disable=E1101
            resp_model.reassign_hashes()

    def _should_be_buttons(self, resp_should_be):
        """
        given an individual should_be, generate the appropriate radio buttons
        """

        # default to filling in the correct bubble
        context = {
            "check_correct": "checked=\"True\"",
            "check_incorrect": "",
            "check_error": ""
        }

        if resp_should_be.lower() == "incorrect":
            context = {
                "check_correct": "",
                "check_incorrect": "checked=\"True\"",
                "check_error": ""
            }
        elif resp_should_be.lower() == "error":
            context = {
                "check_correct": "",
                "check_incorrect": "",
                "check_error": "checked=\"True\""
            }

        return render_to_string('content_testing/form_bottom.html', context)

    def _evaluate(self, response_dict):
        """
        Give the capa_problem the response dictionary and return the result
        """

        # instantiate the capa problem so it can grade itself
        capa = self.capa_problem
        try:
            grade_dict = capa.grade_answers(response_dict)
            return grade_dict

        # if there is any error, we just return None
        except Exception:  # pylint: disable=W0703
            return None

    def _make_verdict(self, correct_map):
        """
        compare what the result of the grading should be with the actual grading
        and return the verdict
        """

        # if there was an error
        if correct_map is None:
            # if we want error, return pass
            if self.should_be == self.ERROR:
                return self.PASS
            return self.ERROR

        # this will all change because self.shuold_be will become a dictionary!!
        passing_all = True
        for grade in correct_map.get_dict().values():
            if grade['correctness'] == 'incorrect':
                passing_all = False
                break

        if (self.should_be.lower() == 'correct' and passing_all) or (self.should_be.lower() == 'incorrect' and not(passing_all)):  # pylint: disable=E1101
            return self.PASS
        else:
            return self.FAIL

    def _get_response_dictionary(self):
        """
        create dictionary to be submitted to the grading function
        """

        # assume integrity has been maintained!!
        resp_dict = self.response_dict

        # unpickle if necessary
        if isinstance(resp_dict, basestring):
            resp_dict = pickle.loads(resp_dict)

        return resp_dict

    def _remake_dict_from_children(self):
        """
        build the response dictionary by getting the values from the children
        """

        # refetch the answers from all the children
        resp_dict = {}
        for resp_model in self.response_set.all():  # pylint: disable=E1101
            for input_model in resp_model.input_set.all():  # pylint: disable=E1101
                resp_dict[input_model.string_id] = input_model.answer

        # update the dictionary
        self.response_dict = resp_dict
        self.save()

    def _create_children(self):
        """
        create child responses and input entries
        """
        # create a preview capa problem
        problem_capa = self.capa_problem

        # go through responder objects
        for responder in problem_capa.responders.itervalues():
            self._create_child(responder, self._get_response_dictionary())

    def _create_child(self, responder, response_dict=dict()):
        """
        from a responder object, create the associated child response model
        """

        # put the response object in the database
        response_model = Response.objects.create(
            content_test=self,
            xml_hash=hash_xml(responder.xml),
            string_id=responder.id)

        # tell it to put its children in the database
        response_model.create_children(responder, response_dict)

    def _update_dictionary(self, new_dict):
        """
        update the input models with the new responses
        """

        # for resp_model in self.response_set.all():
        for input_model in self.input_set.all():  # pylint: disable=E1101
            input_model.answer = new_dict[input_model.string_id]
            input_model.save()


class Response(models.Model):
    """
    Object that corresponds to the <_____response> fields
    """
    # the tests in which this response resides
    content_test = models.ForeignKey(ContentTest)

    # the string identifier
    string_id = models.CharField(max_length=100)

    # hash of the xml for mathcing purposes
    xml_hash = models.BigIntegerField()

    def rematch(self, responder):
        """
        reassociates the ids with this new responder object.
        It is assumed that the hashes match, and all that need
        changing are the ids.
        """

        # if the ids match, we are done
        if self.string_id == responder.id:
            return

        # reassociate the response id
        self.string_id = responder.id

        # rematch all the childrens ids
        input_models = self.input_set.order_by('input_index').all()  # pylint: disable=E1101
        for input_field, input_model in zip(responder.inputfields, input_models):

            # reassign the other ids
            input_model.response_index = input_field.attrib['response_id']
            input_model.string_id = input_field.attrib['id']

            # save the result
            input_model.save()

        self.save()

    def create_children(self, resp_obj=None, response_dict={}):
        '''generate the database entries for the inputs to this response'''

        # see if we need to construct the object from database
        if resp_obj is None:
            resp_obj = self.capa_response

        # go through inputs in this response object
        for entry in resp_obj.inputfields:
            # create the input models
            Input.objects.create(
                response=self,
                content_test=self.content_test,
                string_id=entry.attrib['id'],
                response_index=entry.attrib['response_id'],
                input_index=entry.attrib['answer_id'],
                answer=response_dict.get(entry.attrib['id'], ''))

    @property
    def capa_response(self):
        """
        get the capa-response object to which this response model corresponds
        """
        parent_capa = self.content_test.capa_problem  # pylint: disable=E1101
        self_capa = parent_capa.responders_by_id[self.string_id]
        return self_capa

    def still_matches(self):
        """
        check that the model has the same structure as corresponding responder object
        """

        try:
            return len(self.capa_response.inputfields) == self.input_set.count()  # pylint: disable=E1101
        except KeyError:
            return False

    def reassign_hashes(self):
        """
        refresh the stored hash value, since the xml has changed (attribute update)
        but the structure hasn't
        """

        self.xml_hash = hash_xml(self.capa_response.xml)
        self.save()

    def still_hashes_match(self):
        """
        Return true if the self.xml_hash is still the same as the hash of the
        capa response object
        """

        return hash_xml(self.capa_response.xml) == self.xml_hash


class Input(models.Model):
    """
    the input to a Response
    """

    # The response in which this input lives
    response = models.ForeignKey(Response)

    # The test in which this input resides (grandchild)
    content_test = models.ForeignKey(ContentTest)

    # sequence (first response field, second, etc)
    string_id = models.CharField(max_length=100, editable=False)

    # number for the response that this input is in
    response_index = models.PositiveSmallIntegerField()

    # number for the place this input is in the response
    input_index = models.PositiveSmallIntegerField()

    # the input, supposed a string
    answer = models.CharField(max_length=50, blank=True)
