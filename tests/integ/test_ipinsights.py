# Copyright 2017-2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from __future__ import absolute_import

import os
import pytest

from sagemaker import IPInsights, IPInsightsModel
from sagemaker.predictor import RealTimePredictor
from sagemaker.utils import name_from_base
from tests.integ import DATA_DIR, TRAINING_DEFAULT_TIMEOUT_MINUTES
from tests.integ.record_set import prepare_record_set_from_local_files
from tests.integ.timeout import timeout, timeout_and_delete_endpoint_by_name

FEATURE_DIM = None


@pytest.mark.continuous_testing
def test_ipinsights(sagemaker_session):
    with timeout(minutes=TRAINING_DEFAULT_TIMEOUT_MINUTES):
        data_path = os.path.join(DATA_DIR, 'ipinsights')
        data_filename = 'train.csv'

        with open(os.path.join(data_path, data_filename), 'rb') as f:
            num_records = len(f.readlines())

        ipinsights = IPInsights(
            role='SageMakerRole',
            train_instance_count=1,
            train_instance_type='ml.c4.xlarge',
            num_entity_vectors=10,
            vector_dim=100,
            sagemaker_session=sagemaker_session,
            base_job_name='test-ipinsights')

        record_set = prepare_record_set_from_local_files(data_path, ipinsights.data_location,
                                                         num_records, FEATURE_DIM, sagemaker_session)
        ipinsights.fit(record_set, None)

    endpoint_name = name_from_base('ipinsights')
    with timeout_and_delete_endpoint_by_name(endpoint_name, sagemaker_session):
        model = IPInsightsModel(ipinsights.model_data, role='SageMakerRole', sagemaker_session=sagemaker_session)
        predictor = model.deploy(1, 'ml.c4.xlarge', endpoint_name=endpoint_name)
        assert isinstance(predictor, RealTimePredictor)

        predict_input = [['user_1', '1.1.1.1']]
        result = predictor.predict(predict_input)

        assert len(result) == 1
        for record in result:
            assert record.label["dot_product"] is not None
