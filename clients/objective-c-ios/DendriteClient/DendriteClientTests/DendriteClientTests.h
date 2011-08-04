//
//  DendriteClientTests.h
//  DendriteClientTests
//
//  Created by Jeremy Archer on 7/29/11.
//  Copyright 2011 University of Chicago CI. All rights reserved.
//

#import <SenTestingKit/SenTestingKit.h>
#import "DendriteClient.h"
#import "BlockingTestHelper.h"

@interface DendriteClientTests : SenTestCase <DendriteClientDelegate> {
    DendriteClient * client;
    BlockingTestHelper * testHelper;
}

@end
