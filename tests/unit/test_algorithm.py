# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import copy
import datetime

import pytest
from mock import Mock, patch

from sagemaker.algorithm import AlgorithmEstimator
from sagemaker.estimator import _TrainingJob
from sagemaker.transformer import Transformer

DESCRIBE_ALGORITHM_RESPONSE = {
    'AlgorithmName': 'scikit-decision-trees',
    'AlgorithmArn': 'arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
    'AlgorithmDescription': 'Decision trees using Scikit',
    'CreationTime': datetime.datetime(2018, 8, 3, 22, 44, 54, 437000),
    'TrainingSpecification': {
        'TrainingImage': '123.dkr.ecr.us-east-2.amazonaws.com/decision-trees-sample@sha256:12345',
        'TrainingImageDigest': 'sha256:206854b6ea2f0020d216311da732010515169820b898ec29720bcf1d2b46806a',
        'SupportedHyperParameters': [
            {
                'Name': 'max_leaf_nodes',
                'Description': 'Grow a tree with max_leaf_nodes in best-first fashion.',
                'Type': 'Integer',
                'Range': {
                    'IntegerParameterRangeSpecification': {'MinValue': '1', 'MaxValue': '100000'}
                },
                'IsTunable': True,
                'IsRequired': False,
                'DefaultValue': '100',
            },
            {
                'Name': 'free_text_hp1',
                'Description': 'You can write anything here',
                'Type': 'FreeText',
                'IsTunable': False,
                'IsRequired': True
            }
        ],
        'SupportedTrainingInstanceTypes': ['ml.m4.xlarge', 'ml.m4.2xlarge', 'ml.m4.4xlarge'],
        'SupportsDistributedTraining': False,
        'MetricDefinitions': [
            {'Name': 'validation:accuracy', 'Regex': 'validation-accuracy: (\\S+)'}
        ],
        'TrainingChannels': [
            {
                'Name': 'training',
                'Description': 'Input channel that provides training data',
                'IsRequired': True,
                'SupportedContentTypes': ['text/csv'],
                'SupportedCompressionTypes': ['None'],
                'SupportedInputModes': ['File'],
            }
        ],
        'SupportedTuningJobObjectiveMetrics': [
            {'Type': 'Maximize', 'MetricName': 'validation:accuracy'}
        ],
    },
    'InferenceSpecification': {
        'InferenceImage': '123.dkr.ecr.us-east-2.amazonaws.com/decision-trees-sample@sha256:123',
        'SupportedTransformInstanceTypes': ['ml.m4.xlarge', 'ml.m4.2xlarge'],
        'SupportedContentTypes': ['text/csv'],
        'SupportedResponseMIMETypes': ['text'],
    },
    'ValidationSpecification': {
        'ValidationRole': 'arn:aws:iam::764419575721:role/SageMakerRole',
        'ValidationProfiles': [
            {
                'ProfileName': 'ValidationProfile1',
                'TrainingJobDefinition': {
                    'TrainingInputMode': 'File',
                    'HyperParameters': {},
                    'InputDataConfig': [
                        {
                            'ChannelName': 'training',
                            'DataSource': {
                                'S3DataSource': {
                                    'S3DataType': 'S3Prefix',
                                    'S3Uri': 's3://sagemaker-us-east-2-7123/-scikit-byo-iris/training-input-data',
                                    'S3DataDistributionType': 'FullyReplicated',
                                }
                            },
                            'ContentType': 'text/csv',
                            'CompressionType': 'None',
                            'RecordWrapperType': 'None',
                        }
                    ],
                    'OutputDataConfig': {
                        'KmsKeyId': '',
                        'S3OutputPath': 's3://sagemaker-us-east-2-764419575721/DEMO-scikit-byo-iris/training-output',
                    },
                    'ResourceConfig': {
                        'InstanceType': 'ml.c4.xlarge',
                        'InstanceCount': 1,
                        'VolumeSizeInGB': 10,
                    },
                    'StoppingCondition': {'MaxRuntimeInSeconds': 3600},
                },
                'TransformJobDefinition': {
                    'MaxConcurrentTransforms': 0,
                    'MaxPayloadInMB': 0,
                    'TransformInput': {
                        'DataSource': {
                            'S3DataSource': {
                                'S3DataType': 'S3Prefix',
                                'S3Uri': 's3://sagemaker-us-east-2/scikit-byo-iris/batch-inference/transform_test.csv',
                            }
                        },
                        'ContentType': 'text/csv',
                        'CompressionType': 'None',
                        'SplitType': 'Line',
                    },
                    'TransformOutput': {
                        'S3OutputPath': 's3://sagemaker-us-east-2-764419575721/scikit-byo-iris/batch-transform-output',
                        'Accept': 'text/csv',
                        'AssembleWith': 'Line',
                        'KmsKeyId': '',
                    },
                    'TransformResources': {'InstanceType': 'ml.c4.xlarge', 'InstanceCount': 1},
                },
            }
        ],
        'ValidationOutputS3Prefix': 's3://sagemaker-us-east-2-764419575721/DEMO-scikit-byo-iris/validation-output',
        'ValidateForMarketplace': True,
    },
    'AlgorithmStatus': 'Completed',
    'AlgorithmStatusDetails': {
        'ValidationStatuses': [{'ProfileName': 'ValidationProfile1', 'Status': 'Completed'}]
    },
    'ResponseMetadata': {
        'RequestId': 'e04bc28b-61b6-4486-9106-0edf07f5649c',
        'HTTPStatusCode': 200,
        'HTTPHeaders': {
            'x-amzn-requestid': 'e04bc28b-61b6-4486-9106-0edf07f5649c',
            'content-type': 'application/x-amz-json-1.1',
            'content-length': '3949',
            'date': 'Fri, 03 Aug 2018 23:08:43 GMT',
        },
        'RetryAttempts': 0,
    },
}


def test_algorithm_supported_input_mode_with_valid_input_types(sagemaker_session):
    # verify that the Estimator verifies the
    # input mode that an Algorithm supports.

    file_mode_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    file_mode_algo['TrainingSpecification']['TrainingChannels'] = [
        {
            'Name': 'training',
            'Description': 'Input channel that provides training data',
            'IsRequired': True,
            'SupportedContentTypes': ['text/csv'],
            'SupportedCompressionTypes': ['None'],
            'SupportedInputModes': ['File'],
        },
        {
            'Name': 'validation',
            'Description': 'Input channel that provides validation data',
            'IsRequired': False,
            'SupportedContentTypes': ['text/csv'],
            'SupportedCompressionTypes': ['None'],
            'SupportedInputModes': ['File', 'Pipe'],
        },
    ]

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=file_mode_algo)

    # Creating a File mode Estimator with a File mode algorithm should work
    AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    pipe_mode_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    pipe_mode_algo['TrainingSpecification']['TrainingChannels'] = [
        {
            'Name': 'training',
            'Description': 'Input channel that provides training data',
            'IsRequired': True,
            'SupportedContentTypes': ['text/csv'],
            'SupportedCompressionTypes': ['None'],
            'SupportedInputModes': ['Pipe'],
        },
        {
            'Name': 'validation',
            'Description': 'Input channel that provides validation data',
            'IsRequired': False,
            'SupportedContentTypes': ['text/csv'],
            'SupportedCompressionTypes': ['None'],
            'SupportedInputModes': ['File', 'Pipe'],
        },
    ]

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=pipe_mode_algo)

    # Creating a Pipe mode Estimator with a Pipe mode algorithm should work.
    AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.xlarge',
        train_instance_count=1,
        input_mode='Pipe',
        sagemaker_session=sagemaker_session,
    )

    any_input_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    any_input_algo['TrainingSpecification']['TrainingChannels'] = [
        {
            'Name': 'training',
            'Description': 'Input channel that provides training data',
            'IsRequired': True,
            'SupportedContentTypes': ['text/csv'],
            'SupportedCompressionTypes': ['None'],
            'SupportedInputModes': ['File', 'Pipe'],
        },
        {
            'Name': 'validation',
            'Description': 'Input channel that provides validation data',
            'IsRequired': False,
            'SupportedContentTypes': ['text/csv'],
            'SupportedCompressionTypes': ['None'],
            'SupportedInputModes': ['File', 'Pipe'],
        },
    ]

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=any_input_algo)

    # Creating a File mode Estimator with an algorithm that supports both input modes
    # should work.
    AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )


def test_algorithm_supported_input_mode_with_bad_input_types(sagemaker_session):
    # verify that the Estimator verifies raises exceptions when
    # attempting to train with an incorrect input type

    file_mode_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    file_mode_algo['TrainingSpecification']['TrainingChannels'] = [
        {
            'Name': 'training',
            'Description': 'Input channel that provides training data',
            'IsRequired': True,
            'SupportedContentTypes': ['text/csv'],
            'SupportedCompressionTypes': ['None'],
            'SupportedInputModes': ['File'],
        },
        {
            'Name': 'validation',
            'Description': 'Input channel that provides validation data',
            'IsRequired': False,
            'SupportedContentTypes': ['text/csv'],
            'SupportedCompressionTypes': ['None'],
            'SupportedInputModes': ['File', 'Pipe'],
        },
    ]

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=file_mode_algo)

    # Creating a Pipe mode Estimator with a File mode algorithm should fail.
    with pytest.raises(ValueError):
        AlgorithmEstimator(
            algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
            role='SageMakerRole',
            train_instance_type='ml.m4.xlarge',
            train_instance_count=1,
            input_mode='Pipe',
            sagemaker_session=sagemaker_session,
        )

    pipe_mode_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    pipe_mode_algo['TrainingSpecification']['TrainingChannels'] = [
        {
            'Name': 'training',
            'Description': 'Input channel that provides training data',
            'IsRequired': True,
            'SupportedContentTypes': ['text/csv'],
            'SupportedCompressionTypes': ['None'],
            'SupportedInputModes': ['Pipe'],
        },
        {
            'Name': 'validation',
            'Description': 'Input channel that provides validation data',
            'IsRequired': False,
            'SupportedContentTypes': ['text/csv'],
            'SupportedCompressionTypes': ['None'],
            'SupportedInputModes': ['File', 'Pipe'],
        },
    ]

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=pipe_mode_algo)

    # Creating a File mode Estimator with a Pipe mode algorithm should fail.
    with pytest.raises(ValueError):
        AlgorithmEstimator(
            algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
            role='SageMakerRole',
            train_instance_type='ml.m4.xlarge',
            train_instance_count=1,
            sagemaker_session=sagemaker_session,
        )


@patch('sagemaker.estimator.EstimatorBase.fit', Mock())
def test_algorithm_trainining_channels_with_expected_channels(sagemaker_session):
    training_channels = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)

    training_channels['TrainingSpecification']['TrainingChannels'] = [
        {
            'Name': 'training',
            'Description': 'Input channel that provides training data',
            'IsRequired': True,
            'SupportedContentTypes': ['text/csv'],
            'SupportedCompressionTypes': ['None'],
            'SupportedInputModes': ['File'],
        },
        {
            'Name': 'validation',
            'Description': 'Input channel that provides validation data',
            'IsRequired': False,
            'SupportedContentTypes': ['text/csv'],
            'SupportedCompressionTypes': ['None'],
            'SupportedInputModes': ['File'],
        },
    ]

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=training_channels)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    # Pass training and validation channels. This should work
    estimator.fit({'training': 's3://some/place', 'validation': 's3://some/other'})

    # Passing only the training channel. Validation is optional so this should also work.
    estimator.fit({'training': 's3://some/place'})


@patch('sagemaker.estimator.EstimatorBase.fit', Mock())
def test_algorithm_trainining_channels_with_invalid_channels(sagemaker_session):
    training_channels = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)

    training_channels['TrainingSpecification']['TrainingChannels'] = [
        {
            'Name': 'training',
            'Description': 'Input channel that provides training data',
            'IsRequired': True,
            'SupportedContentTypes': ['text/csv'],
            'SupportedCompressionTypes': ['None'],
            'SupportedInputModes': ['File'],
        },
        {
            'Name': 'validation',
            'Description': 'Input channel that provides validation data',
            'IsRequired': False,
            'SupportedContentTypes': ['text/csv'],
            'SupportedCompressionTypes': ['None'],
            'SupportedInputModes': ['File'],
        },
    ]

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=training_channels)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    # Passing only validation should fail as training is required.
    with pytest.raises(ValueError):
        estimator.fit({'validation': 's3://some/thing'})

    # Passing an unknown channel should fail???
    with pytest.raises(ValueError):
        estimator.fit({'training': 's3://some/data', 'training2': 's3://some/other/data'})


def test_algorithm_train_instance_types_valid_instance_types(sagemaker_session):
    describe_algo_response = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    train_instance_types = ['ml.m4.xlarge', 'ml.m5.2xlarge']

    describe_algo_response['TrainingSpecification'][
        'SupportedTrainingInstanceTypes'
    ] = train_instance_types

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(
        return_value=describe_algo_response
    )

    AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m5.2xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )


def test_algorithm_train_instance_types_invalid_instance_types(sagemaker_session):
    describe_algo_response = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    train_instance_types = ['ml.m4.xlarge', 'ml.m5.2xlarge']

    describe_algo_response['TrainingSpecification'][
        'SupportedTrainingInstanceTypes'
    ] = train_instance_types

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(
        return_value=describe_algo_response
    )

    # invalid instance type, should fail
    with pytest.raises(ValueError):
        AlgorithmEstimator(
            algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
            role='SageMakerRole',
            train_instance_type='ml.m4.8xlarge',
            train_instance_count=1,
            sagemaker_session=sagemaker_session,
        )


def test_algorithm_distributed_training_validation(sagemaker_session):
    distributed_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    distributed_algo['TrainingSpecification']['SupportsDistributedTraining'] = True

    single_instance_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    single_instance_algo['TrainingSpecification']['SupportsDistributedTraining'] = False

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=distributed_algo)

    # Distributed training should work for Distributed and Single instance.
    AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.xlarge',
        train_instance_count=2,
        sagemaker_session=sagemaker_session,
    )

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=single_instance_algo)

    # distributed training on a single instance algorithm should fail.
    with pytest.raises(ValueError):
        AlgorithmEstimator(
            algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
            role='SageMakerRole',
            train_instance_type='ml.m5.2xlarge',
            train_instance_count=2,
            sagemaker_session=sagemaker_session,
        )


def test_algorithm_hyperparameter_integer_range_valid_range(sagemaker_session):
    hyperparameters = [
        {
            'Description': 'Grow a tree with max_leaf_nodes in best-first fashion.',
            'Type': 'Integer',
            'Name': 'max_leaf_nodes',
            'Range': {
                'IntegerParameterRangeSpecification': {'MinValue': '1', 'MaxValue': '100000'}
            },
            'IsTunable': True,
            'IsRequired': False,
            'DefaultValue': '100',
        }
    ]

    some_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    some_algo['TrainingSpecification']['SupportedHyperParameters'] = hyperparameters

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=some_algo)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.2xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    estimator.set_hyperparameters(max_leaf_nodes=1)
    estimator.set_hyperparameters(max_leaf_nodes=100000)


def test_algorithm_hyperparameter_integer_range_invalid_range(sagemaker_session):
    hyperparameters = [
        {
            'Description': 'Grow a tree with max_leaf_nodes in best-first fashion.',
            'Type': 'Integer',
            'Name': 'max_leaf_nodes',
            'Range': {
                'IntegerParameterRangeSpecification': {'MinValue': '1', 'MaxValue': '100000'}
            },
            'IsTunable': True,
            'IsRequired': False,
            'DefaultValue': '100',
        }
    ]

    some_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    some_algo['TrainingSpecification']['SupportedHyperParameters'] = hyperparameters

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=some_algo)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.2xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    with pytest.raises(ValueError):
        estimator.set_hyperparameters(max_leaf_nodes=0)

    with pytest.raises(ValueError):
        estimator.set_hyperparameters(max_leaf_nodes=100001)


def test_algorithm_hyperparameter_continuous_range_valid_range(sagemaker_session):
    hyperparameters = [
        {
            'Description': 'A continuous hyperparameter',
            'Type': 'Continuous',
            'Name': 'max_leaf_nodes',
            'Range': {
                'ContinuousParameterRangeSpecification': {'MinValue': '0.0', 'MaxValue': '1.0'}
            },
            'IsTunable': True,
            'IsRequired': False,
            'DefaultValue': '100',
        }
    ]

    some_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    some_algo['TrainingSpecification']['SupportedHyperParameters'] = hyperparameters

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=some_algo)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.2xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    estimator.set_hyperparameters(max_leaf_nodes=0)
    estimator.set_hyperparameters(max_leaf_nodes=1.0)
    estimator.set_hyperparameters(max_leaf_nodes=0.5)
    estimator.set_hyperparameters(max_leaf_nodes=1)


def test_algorithm_hyperparameter_continuous_range_invalid_range(sagemaker_session):
    hyperparameters = [
        {
            'Description': 'A continuous hyperparameter',
            'Type': 'Continuous',
            'Name': 'max_leaf_nodes',
            'Range': {
                'ContinuousParameterRangeSpecification': {'MinValue': '0.0', 'MaxValue': '1.0'}
            },
            'IsTunable': True,
            'IsRequired': False,
            'DefaultValue': '100',
        }
    ]

    some_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    some_algo['TrainingSpecification']['SupportedHyperParameters'] = hyperparameters

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=some_algo)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.2xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    with pytest.raises(ValueError):
        estimator.set_hyperparameters(max_leaf_nodes=1.1)

    with pytest.raises(ValueError):
        estimator.set_hyperparameters(max_leaf_nodes=-0.1)


def test_algorithm_hyperparameter_categorical_range(sagemaker_session):
    hyperparameters = [
        {
            'Description': 'A continuous hyperparameter',
            'Type': 'Categorical',
            'Name': 'hp1',
            'Range': {'CategoricalParameterRangeSpecification': {'Values': ['TF', 'MXNet']}},
            'IsTunable': True,
            'IsRequired': False,
            'DefaultValue': '100',
        }
    ]

    some_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    some_algo['TrainingSpecification']['SupportedHyperParameters'] = hyperparameters

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=some_algo)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.2xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    estimator.set_hyperparameters(hp1='MXNet')
    estimator.set_hyperparameters(hp1='TF')

    with pytest.raises(ValueError):
        estimator.set_hyperparameters(hp1='Chainer')

    with pytest.raises(ValueError):
        estimator.set_hyperparameters(hp1='MxNET')


def test_algorithm_required_hyperparameters_not_provided(sagemaker_session):
    hyperparameters = [
        {
            'Description': 'A continuous hyperparameter',
            'Type': 'Categorical',
            'Name': 'hp1',
            'Range': {'CategoricalParameterRangeSpecification': {'Values': ['TF', 'MXNet']}},
            'IsTunable': True,
            'IsRequired': True,
        },
        {
            'Name': 'hp2',
            'Description': 'A continuous hyperparameter',
            'Type': 'Categorical',
            'IsTunable': False,
            'IsRequired': True
        }
    ]

    some_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    some_algo['TrainingSpecification']['SupportedHyperParameters'] = hyperparameters

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=some_algo)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.2xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    # hp1 is required and was not provided
    with pytest.raises(ValueError):
        estimator.set_hyperparameters(hp2='TF2')

    # Calling fit with unset required hyperparameters should fail
    # this covers the use case of not calling set_hyperparameters() explicitly
    with pytest.raises(ValueError):
        estimator.fit({'training': 's3://some/place'})


@patch('sagemaker.estimator.EstimatorBase.fit', Mock())
def test_algorithm_required_hyperparameters_are_provided(sagemaker_session):
    hyperparameters = [
        {
            'Description': 'A categorical hyperparameter',
            'Type': 'Categorical',
            'Name': 'hp1',
            'Range': {'CategoricalParameterRangeSpecification': {'Values': ['TF', 'MXNet']}},
            'IsTunable': True,
            'IsRequired': True,
        },
        {
            'Name': 'hp2',
            'Description': 'A categorical hyperparameter',
            'Type': 'Categorical',
            'IsTunable': False,
            'IsRequired': True
        },
        {
            'Name': 'free_text_hp1',
            'Description': 'You can write anything here',
            'Type': 'FreeText',
            'IsTunable': False,
            'IsRequired': True
        }
    ]

    some_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    some_algo['TrainingSpecification']['SupportedHyperParameters'] = hyperparameters

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=some_algo)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.2xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    # All 3 Hyperparameters are provided
    estimator.set_hyperparameters(hp1='TF', hp2='TF2', free_text_hp1='Hello!')


def test_algorithm_required_free_text_hyperparameter_not_provided(sagemaker_session):
    hyperparameters = [
        {
            'Name': 'free_text_hp1',
            'Description': 'You can write anything here',
            'Type': 'FreeText',
            'IsTunable': False,
            'IsRequired': True
        },
        {
            'Name': 'free_text_hp2',
            'Description': 'You can write anything here',
            'Type': 'FreeText',
            'IsTunable': False,
            'IsRequired': False
        }
    ]

    some_algo = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    some_algo['TrainingSpecification']['SupportedHyperParameters'] = hyperparameters

    sagemaker_session.sagemaker_client.describe_algorithm = Mock(return_value=some_algo)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.2xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    # Calling fit with unset required hyperparameters should fail
    # this covers the use case of not calling set_hyperparameters() explicitly
    with pytest.raises(ValueError):
        estimator.fit({'training': 's3://some/place'})

    # hp1 is required and was not provided
    with pytest.raises(ValueError):
        estimator.set_hyperparameters(free_text_hp2='some text')


@patch('sagemaker.algorithm.AlgorithmEstimator.create_model')
def test_algorithm_create_transformer(create_model, sagemaker_session):
    sagemaker_session.sagemaker_client.describe_algorithm = Mock(
        return_value=DESCRIBE_ALGORITHM_RESPONSE)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    estimator.latest_training_job = _TrainingJob(sagemaker_session, 'some-job-name')
    model = Mock()
    model.name = 'my-model'
    create_model.return_value = model

    transformer = estimator.transformer(instance_count=1, instance_type='ml.m4.xlarge')

    assert isinstance(transformer, Transformer)
    create_model.assert_called()
    assert transformer.model_name == 'my-model'


def test_algorithm_create_transformer_without_completed_training_job(sagemaker_session):
    sagemaker_session.sagemaker_client.describe_algorithm = Mock(
        return_value=DESCRIBE_ALGORITHM_RESPONSE)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    with pytest.raises(RuntimeError) as error:
        estimator.transformer(instance_count=1, instance_type='ml.m4.xlarge')
        assert 'No finished training job found associated with this estimator' in str(error)


@patch('sagemaker.algorithm.AlgorithmEstimator.create_model')
def test_algorithm_create_transformer_with_product_id(create_model, sagemaker_session):
    response = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    response['ProductId'] = 'some-product-id'
    sagemaker_session.sagemaker_client.describe_algorithm = Mock(
        return_value=response)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    estimator.latest_training_job = _TrainingJob(sagemaker_session, 'some-job-name')
    model = Mock()
    model.name = 'my-model'
    create_model.return_value = model

    transformer = estimator.transformer(instance_count=1, instance_type='ml.m4.xlarge')
    assert transformer.env is None


def test_algorithm_enable_network_isolation_no_product_id(sagemaker_session):
    sagemaker_session.sagemaker_client.describe_algorithm = Mock(
        return_value=DESCRIBE_ALGORITHM_RESPONSE)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    network_isolation = estimator.enable_network_isolation()
    assert network_isolation is False


def test_algorithm_enable_network_isolation_with_product_id(sagemaker_session):
    response = copy.deepcopy(DESCRIBE_ALGORITHM_RESPONSE)
    response['ProductId'] = 'some-product-id'
    sagemaker_session.sagemaker_client.describe_algorithm = Mock(
        return_value=response)

    estimator = AlgorithmEstimator(
        algorithm_arn='arn:aws:sagemaker:us-east-2:1234:algorithm/scikit-decision-trees',
        role='SageMakerRole',
        train_instance_type='ml.m4.xlarge',
        train_instance_count=1,
        sagemaker_session=sagemaker_session,
    )

    network_isolation = estimator.enable_network_isolation()
    assert network_isolation is True
