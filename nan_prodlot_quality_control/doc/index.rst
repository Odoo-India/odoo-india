
nan_prodlot_quality_control
---------------------------

This module supply an infrastructure to define Quality Test that the
Production Lots must pass in some situations. It adds a workflow to
Production Lot.

Adds a new simple model for Quality Test to define Triggers (a mark to
specify when a test must be passed) a model related to product with
one2many field which define which tests must to pass the lots of the
product specifying the Test Template and the Trigger. In the Company there
are a similar field and one2many to define the general tests (when a
product is created take the default values from these values).
In the Production Lot there are a similar model and one2many field but
relates the Lot with a trigger and Test.

IMPORTANT: This module without anything else do not define any Test to pass
It will be defined in other dependant modules.


